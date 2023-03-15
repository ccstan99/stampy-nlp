"""Hugging Face Utilities

"""
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import logging
import requests
import os
from dotenv import load_dotenv


load_dotenv()


HUGGINGFACE_API = 'https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/'
HUGGINGFACE_QA = 'https://api-inference.huggingface.co/pipeline/question-answering/deepset/electra-base-squad2'

RETRIEVER_MODEL_ID = 'multi-qa-mpnet-base-cos-v1'
LITSEARCH_MODEL_ID = 'allenai-specter'
READER_MODEL_ID = 'deepset/electra-base-squad2'


def api_key():
    key: str = os.getenv('HUGGINGFACE_API_KEY')
    if not key:
        raise Exception("Missing environment variable HUGGINGFACE_API_KEY")
    return key


def api_headers():
    return {'Authorization': f'Bearer {api_key()}'}


RETRIEVER_MODEL = None
def init_retriever():
    """If not yet initialized, load retriever model for general semantic similarity sentence embeddings"""
    logging.debug("init_retriever()")
    # RETRIEVER_ID = '/Users/cheng2/.cache/huggingface/hub/models--sentence-transformers--multi-qa-mpnet-base-cos-v1/snapshots/bd0b4f6d767d5cb937b4c1a9611df492a80e891a'
    RETRIEVER_PATH = './models/retriever'
    print('SentenceTransformer', RETRIEVER_PATH)
    global RETRIEVER_MODEL
    RETRIEVER_MODEL = SentenceTransformer(RETRIEVER_PATH)

    # response = requests.post(HUGGINGFACE_API + model_id,
    #                          headers=HUGGINGFACE_HEADER,
    #                          json={"inputs": query, "options": {"wait_for_model": True}})
    # xq = response.json()[0][0]
    return RETRIEVER_MODEL


READER_MODEL = None
def init_reader():
    """If not yet initialized, load reader model for extracting answer to question given context"""
    logging.debug("init_reader()")
    READER_PATH = './models/reader'
    print('question-answering pipeline', READER_PATH)
    global READER_MODEL
    READER_MODEL = pipeline('question-answering',
                            model=READER_PATH, tokenizer=READER_PATH)
    # response = requests.post(HUGGINGFACE_QA,
    #                          headers=HUGGINGFACE_HEADER,
    #                          json={"inputs": {"question": query, "context": context},
    #                                "options": {"wait_for_model": True}})
    # response = response.json()
    return READER_MODEL


def get_retriever():
    if not RETRIEVER_MODEL:
        init_retriever()
    return RETRIEVER_MODEL


def get_reader():
    if not READER_MODEL:
        init_reader()
    return READER_MODEL


def embed_text(model, titles):
    """Create vector embedding from list of titles using model"""
    logging.debug("embed_text()")
    encodings = model.encode(titles, show_progress_bar=True)
    # normalize depending on model with or without cosine
    # encodings = normalize(encodings)
    return encodings


def lit_search(query):
    """Create vector embedding from list of titles using model"""
    logging.debug("lit_search(%s)", query)
    response = requests.post(HUGGINGFACE_API + LITSEARCH_MODEL_ID,
                             headers=api_headers(),
                             json={'inputs': query + '[SEP]', "options": {'wait_for_model': True}})
    return response.json()
