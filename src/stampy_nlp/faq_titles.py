from sentence_transformers import SentenceTransformer, util
import stampy_nlp.utilities.pinecone_utils as dbutils
import stampy_nlp.utilities.coda_utils as codautils
import stampy_nlp.utilities.huggingface_utils as hfutils
import logging
import json
import sys


COUNT: int = 3
MAX_DUPLICATES:int = 100
DEFAULT_TOPK: int = dbutils.DEFAULT_TOPK
MODEL_ID: str = 'multi-qa-mpnet-base-cos-v1'
delete_all: bool = False


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
    duplicates = duplicates[:MAX_DUPLICATES]
    with open('stampy-duplicates.json', 'w') as f:
        json.dump(duplicates, f)
    return duplicates


def encode_faq_titles():
    """Pull FAQ from Coda, embed titles, find duplicates, then store in Pinecone DB"""
    try:
        data = codautils.get_df_data()
        logging.debug(f"data.index {data.index[:COUNT]}")
    except Exception as e:
        logging.error(f'Failed get_df_data() reading from Coda.')
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
        embeddings = hfutils.embed_text(model, data['title']).tolist()
        metadata = json.loads(data.to_json(orient='records'))
        logging.debug(f"metadata {metadata[:COUNT]}")
    except Exception as e:
        logging.error("Failed embed_text")
        raise(e)

    try:
        dbutils.upload_data(data.index.tolist(), embeddings, metadata, delete_all=delete_all)
    except Exception as e:
        logging.error("Failed upload_data to pinecone")
        raise(e)

    return duplicates


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) > 1 and sys.argv[1] == '-delete-all':
        logging.debug(f"sys.argv[1]={sys.argv[1]}")
        delete_all = True
    logging.debug(f"delete_all={delete_all}")

    encode_faq_titles()
