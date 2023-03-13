"""Hugging Face Utilities

"""
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import logging
import requests
import os

HUGGINGFACE_API_KEY: str = os.getenv('HUGGINGFACE_API_KEY')
if (HUGGINGFACE_API_KEY == None):
    raise Exception("Missing environment variable HUGGINGFACE_API_KEY")

HUGGINGFACE_API = 'https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/'
HUGGINGFACE_QA = 'https://api-inference.huggingface.co/pipeline/question-answering/deepset/electra-base-squad2'
HUGGINGFACE_HEADER = {'Authorization': f'Bearer {HUGGINGFACE_API_KEY}'}

RETRIEVER_MODEL_ID = 'multi-qa-mpnet-base-cos-v1'
LITSEARCH_MODEL_ID = 'allenai-specter'
READER_MODEL_ID = 'deepset/electra-base-squad2'


def init_retriever():
    """If not yet initialized, load retriever model for general semantic similarity sentence embeddings"""
    logging.debug(f"init_retriever()")
    # RETRIEVER_ID = '/Users/cheng2/.cache/huggingface/hub/models--sentence-transformers--multi-qa-mpnet-base-cos-v1/snapshots/bd0b4f6d767d5cb937b4c1a9611df492a80e891a'
    RETRIEVER_PATH = './models/retriever'
    print('SentenceTransformer', RETRIEVER_PATH)
    RETRIEVER_MODEL = SentenceTransformer(RETRIEVER_PATH)

    # response = requests.post(HUGGINGFACE_API + model_id,
    #                          headers=HUGGINGFACE_HEADER,
    #                          json={"inputs": query, "options": {"wait_for_model": True}})
    # xq = response.json()[0][0]
    return RETRIEVER_MODEL


def init_reader():
    """If not yet initialized, load reader model for extracting answer to question given context"""
    logging.debug(f"init_reader()")
    READER_PATH = './models/reader'
    print('question-answering pipeline', READER_PATH)
    READER_MODEL = pipeline('question-answering',
                            model=READER_PATH, tokenizer=READER_PATH)
    # response = requests.post(HUGGINGFACE_QA,
    #                          headers=HUGGINGFACE_HEADER,
    #                          json={"inputs": {"question": query, "context": context},
    #                                "options": {"wait_for_model": True}})
    # response = response.json()
    return READER_MODEL


def embed_text(model, titles):
    """Create vector embedding from list of titles using model"""
    logging.debug(f"embed_text()")
    encodings = model.encode(titles, show_progress_bar=True)
    # normalize depending on model with or without cosine
    # encodings = normalize(encodings)
    return encodings


def lit_search(query):
    """Create vector embedding from list of titles using model"""
    logging.debug(f"lit_search({query})")
    response = requests.post(HUGGINGFACE_API + LITSEARCH_MODEL_ID,
                             headers=HUGGINGFACE_HEADER,
                             json={'inputs': query + '[SEP]', "options": {'wait_for_model': True}})
    return response.json()
