from sentence_transformers import SentenceTransformer, util
import pandas as pd
import pinecone
import logging
import requests
import os
import json

CODA_TOKEN: str = os.getenv('CODA_TOKEN')
if (CODA_TOKEN == None):
    raise Exception("Missing environment variable CODA_TOKEN")

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
if (PINECONE_API_KEY == None):
    raise Exception("Missing environment variable PINECONE_API_KEY")

GCP_ENV: str = 'us-west1-gcp'
PINECONE_INDEX: str = 'alignment-lit'
PINECONE_NAMESPACE: str = 'faq-titles'
MODEL_ID: str = 'multi-qa-mpnet-base-cos-v1'

CODA_DOC_ID: str = 'fau7sl2hmG'
TABLE_ID: str = 'Answers'
COUNT: int = 3


def get_df_data():
    """Fetches questions from Coda and returns a pandas dataframe for processing"""
    logging.debug(f"get_df_data()")
    url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{TABLE_ID}/rows'
    headers = {'Authorization': f'Bearer {CODA_TOKEN}'}
    params = {
        'useColumnNames': True,
        'limit': 1000
    }
    json_items = requests.get(url, headers=headers,
                              params=params).json()['items']

    data_list = []
    for item in json_items:
        values = item['values']
        pageid = str(values['UI ID']).strip()
        status = values['Status']

        # link to UI if available else use coda link
        if status == 'Live on site':
            url = 'https://aisafety.info?state=' + pageid
        else:
            url = values['Link']

        # add to data_list if some kinds of question, even if unanswered
        if isinstance(pageid, str) and len(pageid) >= 4:
            data_list.append({
                'id': item['id'],
                'title': item['name'],
                'status': status,
                'pageid': pageid,
                'url': url,
            })

    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    return df


def embed_text(model, titles):
    """Create vector embedding from list of titles using model"""
    logging.debug(f"embed_text()")
    encodings = model.encode(titles, show_progress_bar=True)
    # normalize depending on model with or without cosine
    # encodings = normalize(encodings)
    return encodings


def extract_details(df_row):
    """Extract relevant columns given dataframe row"""
    return {
        'title': df_row['title'],
        'url': df_row['url']
    }


def find_duplicates(model, data):
    """Use SentenceTransformer util.paraphrase to find duplicates"""
    logging.debug(f"find_duplicates()")
    titles = data['title']
    mined = util.paraphrase_mining(model, titles, show_progress_bar=True)
    duplicates = list(map(lambda x: {
        'score': x[0],
        'entry1': extract_details(data.iloc[x[1]]),
        'entry2': extract_details(data.iloc[x[2]])
    }, mined))
    with open('stampy-duplicates.json', 'w') as f:
        json.dump(duplicates[:100], f)
    return duplicates


def upload_data(ids, vectors, meta):
    """Upload embeddings to pinecone vector database for faster query"""
    logging.debug(f"upload_data()")
    pinecone.init(api_key=PINECONE_API_KEY, environment=GCP_ENV)
    index = pinecone.Index(PINECONE_INDEX)

    # if PINECONE_INDEX not in pinecone.list_indexes():
    #     pinecone.create_index(name=PINECONE_INDEX, dimension=embeddings.shape[1])
    #     index = pinecone.Index(PINECONE_INDEX)
    # else:
    #     index = pinecone.Index(PINECONE_INDEX)
    #     index.delete(deleteAll=True, namespace=PINECONE_NAMESPACE)

    # upload in smaller batches to avoid errors
    batch_size = 100
    length = len(ids)
    logging.debug(f"upload_data {length}")
    for i in range(0, length, batch_size):
        logging.debug(f"upsert: {PINECONE_NAMESPACE} {i} {i+batch_size}")
        index.upsert(
            list(zip(ids[i:i+batch_size],
                 vectors[i:i+batch_size], meta[i:i+batch_size])),
            namespace=PINECONE_NAMESPACE
        )


def encode_faq_titles():
    """Pull FAQ from Coda, embed titles, find duplicates, then store in Pinecone DB"""
    try:
        data = get_df_data()
        logging.debug(f"data.index {data.index[:COUNT]}")
    except Exception as e:
        logging.error(f'Failed get_df_data reading from Coda.')
        raise(e)

    try:
        model = SentenceTransformer(MODEL_ID)
    except Exception as e:
        logging.error(f"Failed to load SentenceTransformer {MODEL_ID}.")
        raise(e)

    try:
        duplicates = find_duplicates(model, data)
        logging.debug(f"find_duplicates {duplicates[:COUNT]}")
    except Exception as e:
        logging.error("Failed find_duplicates")
        raise(e)

    try:
        embeddings = embed_text(model, data['title']).tolist()
        metadata = json.loads(data.to_json(orient='records'))
        logging.debug(f"metadata {metadata[:COUNT]}")
    except Exception as e:
        logging.error("Failed embed_text")
        raise(e)

    try:
        upload_data(data.index.tolist(), embeddings, metadata)
    except Exception as e:
        logging.error("Failed upload_data to pinecone")
        raise(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    encode_faq_titles()
