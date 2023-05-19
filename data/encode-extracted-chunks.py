import pinecone
from sentence_transformers import SentenceTransformer
import requests
import pandas as pd
import numpy as np
import os
import json
import jsonlines
import re
import markdown
from urllib.parse import urlparse
from bs4 import BeautifulSoup

CODA_TOKEN: str = os.getenv('CODA_TOKEN')
if (CODA_TOKEN == None):
    raise Exception("Missing environment variable CODA_TOKEN")

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
if (PINECONE_API_KEY == None):
    raise Exception("Missing environment variable PINECONE_API_KEY")

GCP_ENV = 'us-west1-gcp'
PINECONE_INDEX = 'alignment-lit'
PINECONE_NAMESPACE = 'extracted-chunks'
# PINECONE_NAMESPACE = 'all-chunks'
MODEL_ID = 'multi-qa-mpnet-base-cos-v1'

CODA_DOC_ID = 'fau7sl2hmG'
TABLE_ID = 'Answers'
COUNT = 5


def get_df_data():
    # url = f'https://coda.io/apis/v1/docs/${CODA_DOC_ID}/tables/${TABLE_ID}/rows?${PARAMS}'
    url = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{TABLE_ID}/rows'
    headers = {'Authorization': f'Bearer {CODA_TOKEN}'}
    params = {'useColumnNames': True, 'limit': 1000}
    json_items = requests.get(url, headers=headers,
                              params=params).json()['items']

    data_list = []
    for item in json_items:
        values = item['values']
        pageid = values['UI ID'].strip()

        # link to UI if available else use coda link
        if values['Status'] == 'Live on site' and len(pageid) >= 4:
            url = 'https://aisafety.info?state=' + pageid

            data_list.append({
                'id': url,
                'source': 'stampy',
                'title': item['name'],
                'text': values['Rich Text'],
                'url': url,
            })

    # print('len(data_list)', len(data_list))
    # json.dump(data_list, open("faq_titles.json", "w"))
    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    # print(df)
    return df


def get_df_arxiv():
    # using pre-filtered set from released 1.0 version
    # where item['source'] == 'arxiv' and item['alignment_text'] == 'pos'
    # 959 records with 1 duplicate id creates 958
    dir = '/mnt/c/Users/euryd/PycharmProjects/data/'
    datafile = 'arxiv_papers_alignment_lit.json'

    data_list = []
    with open(dir + datafile, 'r') as f:
        json_items = json.load(f)
    try:
        for item in json_items:
            keys = item.keys()
            title = item['title']
            abstract = item['abstract']
            text = item['text']
            data_list.append({
                'id': item['paper_version'],
                'source': 'arxiv',
                'title': title,
                'text': abstract,
                'url': item['url'],
            })
    except KeyError:
        pass

    # print('len(data_list)', len(data_list))
    # json.dump(data_list, open("paper_abstracts.json", "w"))
    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    # df.to_csv("paper_abstracts.csv", index=True)
    return df


def get_df_littext():
    dir = '/mnt/c/Users/euryd/PycharmProjects/data/'
    datafile = 'alignment_texts.jsonl'

    quality_sources = ['alignment forum']
    data_list = []
    num_errors = 0
    with jsonlines.open(dir + datafile, "r") as reader:
        for item in reader:
            try:
                keys = item.keys()
                source = ""
                if 'source' in keys:
                    source = item['source']

                if 'printouts' not in keys:
                # if source in quality_sources:
                    title = item['title']
                    text = item['text']

                    url = ""
                    if 'url' in keys:
                        url = item['url']
                    elif 'link' in keys:
                        url = item['link']
                    
                    if len(source) == 0:
                        source = urlparse(url).netloc

                    id = ""
                    if 'id' in keys:
                        id = item['id']
                    elif len(url) > 0:
                        id = url
                    else:
                        id = str(hash(title))

                    data_list.append({
                        'id': id,
                        'source': source,
                        'title': title,
                        'text': text,
                        'url': url,
                    })
            except KeyError as err:
                # print("ERROR:", err, item['text'])
                num_errors += 1
                pass

    print('\n***\nnum_errors', num_errors)
    # print('len(data_list)', len(data_list))
    # json.dump(data_list, open("data_list.json", "w"))
    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    # df.to_csv("data_list.csv", index=True)
    return df


# strip out markdown and html tags to keep text only
def format_text(text):
    # remove '[]()' and extra spaces
    formatted = text
    formatted = re.sub(r'(## Related)|(\[.*\])|(\(.*\))', '', formatted)
    html = markdown.markdown(text)
    # strip off md and html text
    soup = BeautifulSoup(html, 'html.parser')
    formatted = soup.get_text()
    formatted = re.sub(r'(\n)', ' ', formatted)
    formatted = re.sub(r'(\s(\s)+)', ' ', formatted)
    return formatted


def chunk_text(original, min_chunk=100, max_chunk=1000):
    text = format_text(original)
    length = len(text)
    chunks = []
    start = 0
    # print(length, start, chunk_size, text)

    while start < length:
        s = text[start:start + max_chunk]
        # break start & end on periods for complete sentences
        end = s.rfind(".") + 1
        # if no '.' period, take entire chunk
        if end <= 0:
            end = max_chunk
            chunk = s.strip()
        else:
            chunk = text[start:start + end].strip()
        # nothing to add
        if len(chunk) > min_chunk:
            chunks.append(chunk)
            # print(start, start+end, len(chunk), chunk)
        start += end

    return chunks


def format_num(n, digits=3):
    return str(n).zfill(digits)


def embed_text(model, titles):
    encodings = model.encode(titles, show_progress_bar=True)
    # encodings = normalize(encodings)
    return encodings


def upload_data(ids, vectors, meta):
    pinecone.init(api_key=PINECONE_API_KEY, environment=GCP_ENV)
    index = pinecone.Index(PINECONE_INDEX)
    if False:
        index.delete(delete_all=True, namespace=PINECONE_NAMESPACE)

    batch_size = 100
    length = len(ids)
    print('upload_data', length)
    for i in range(0, length, batch_size):
        if length < 1000 or i % 1000 == 0:
            print('upsert:', PINECONE_NAMESPACE, i, i+batch_size)
        index.upsert(
            list(zip(ids[i:i + batch_size], vectors[i:i +
                 batch_size], meta[i:i + batch_size])),
            namespace=PINECONE_NAMESPACE
        )


data = get_df_data()
# data = get_df_arxiv()
# data = get_df_littext()
# print('\nids', data.index[:COUNT])
print('\ndata', data[:COUNT])

data["chunks"] = data["text"].map(chunk_text)
data["idx"] = data["chunks"].map(lambda x: np.arange(len(x)).tolist())
data.to_csv("data_chunks_idx.csv", index=True)

data = data.explode(["idx", "chunks"])
data = data[data["idx"].notnull()]
# print(data)
# print('min-max', data["idx"].min(), data["idx"].max())
data.index = data["idx"].map(format_num) + "-" + data.index
data = data[['title', 'source', 'chunks', 'url']].rename(
    columns={"chunks": "text"})
data.to_csv("data_exploded.csv", index=True)
print(data)
# exit(0)

print('SentenceTransformer', MODEL_ID)
model = SentenceTransformer(MODEL_ID)

print('embed_text')
embeddings = embed_text(model, data['text']).tolist()
metadata = json.loads(data.to_json(orient='records'))
# print('\nmetadata', metadata[:COUNT])

print('upload_data')
upload_data(data.index.tolist(), embeddings, metadata)
