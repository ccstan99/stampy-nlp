import pinecone
from sentence_transformers import SentenceTransformer
import pandas as pd
import logging
import os
import json
import jsonlines

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
if (PINECONE_API_KEY == None):
    raise Exception("Missing environment variable PINECONE_API_KEY")

GCP_ENV = 'us-west1-gcp'
PINECONE_INDEX = 'alignment-lit'
PINECONE_NAMESPACE = 'lit-abstracts'
MODEL_ID = 'allenai-specter'

COUNT = 5


def get_df_data_newscrape():
    # alignment-scrape-clean-2022-11-12 format slightly different from released 1.0 version
    # 1446 records, 894 with abstract, 829 unique ids with multi versions, include non-alignment lit?
    dir = '/mnt/c/Users/euryd/PycharmProjects/data/alignment-scrape-clean-2022-11-12/'
    datafile = 'arxiv_papers.jsonl'
    data_list = []
    with jsonlines.open(dir + datafile, "r") as reader:
        for item in reader:
            try:
                title = item['title']
                abstract = item['abstract']
                data_list.append({
                    'id': item['id'],
                    'title': title,
                    'abstract': abstract,
                    'title-abstract': title + "[SEP]" + abstract,
                    'authors': item['authors'],
                    'url': item['url'],
                    # 'id': item['paper_version'],
                    # 'score': item['confidence_score']
                })
            except KeyError:
                pass

    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    df.to_csv("arxiv_papers_abstract.csv", index=True)
    return df


def get_df_data():
    # using pre-filtered set from released 1.0 version
    # where item['source'] == 'arxiv' and item['alignment_text'] == 'pos'
    # 959 records with 1 duplicate id creates 958
    dir = '/mnt/c/Users/euryd/PycharmProjects/data/'
    datafile = 'arxiv_papers_alignment_lit.json'

    data_list = []
    text_list = []
    with open(dir + datafile, 'r') as f:
        json_items = json.load(f)
    try:
        for item in json_items:
            keys = item.keys()
            title = item['title']
            abstract = item['abstract']
            data_list.append({
                # 'id': item['id'],
                # 'score': item['confidence_score'],
                'id': item['paper_version'],
                'title': title,
                'abstract': abstract,
                'authors': item['authors'],
                'url': item['url'],
            })
            text_list.append(title + "[SEP]" + abstract)
    except KeyError:
        pass

    # print('len(data_list)', len(data_list))
    # json.dump(data_list, open("paper_abstracts.json", "w"))
    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    # df.to_csv("paper_abstracts.csv", index=True)
    return df, text_list


def embed_text(model, titles):
    encodings = model.encode(titles, show_progress_bar=True)
    # encodings = normalize(encodings)
    return encodings


def extract_details(df_row):
    return {
        'id': df_row['id'],
        'title': df_row['title'],
        'abstract': df_row['abstract'],
        'author': df_row['author'],
        'url': df_row['url'],
        'score': df_row['score'],
    }


def upload_data(ids, vectors, meta):
    pinecone.init(api_key=PINECONE_API_KEY, environment=GCP_ENV)
    index = pinecone.Index(PINECONE_INDEX)

    # if PINECONE_INDEX not in pinecone.list_indexes():
    #     pinecone.create_index(name=PINECONE_INDEX, dimension=embeddings.shape[1])
    #     index = pinecone.Index(PINECONE_INDEX)
    # else:
    #     index = pinecone.Index(PINECONE_INDEX)
    #     index.delete(deleteAll=True, namespace=PINECONE_NAMESPACE)

    batch_size = 100
    length = len(ids)
    print('upload_data',  length)
    for i in range(0, length, batch_size):
        # print('upsert:', PINECONE_NAMESPACE, i, i+batch_size)
        index.upsert(
            list(zip(ids[i:i+batch_size],
                 vectors[i:i+batch_size], meta[i:i+batch_size])),
            namespace=PINECONE_NAMESPACE
        )


data, text = get_df_data()
print('SentenceTransformer', MODEL_ID)
model = SentenceTransformer(MODEL_ID)

# print('\nids', data.index[:COUNT])
# print('\ndata', data[:COUNT])
# print('\ntitle-abstract', data['title-abstract'][:COUNT])
print('embed_text')
embeddings = embed_text(model, text).tolist()
metadata = json.loads(data.to_json(orient='records'))
# print('\nmetadata', metadata[:COUNT])

upload_data(data.index.tolist(), embeddings, metadata)
