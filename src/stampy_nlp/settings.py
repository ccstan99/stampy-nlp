import os
from dotenv import load_dotenv


load_dotenv()

CODA_TOKEN: str = os.getenv('CODA_TOKEN')
HUGGINGFACE_API_KEY: str = os.getenv('HUGGINGFACE_API_KEY')
PINECONE_API_KEY: str = os.getenv('PINECONE_API_KEY')

STAMPY_BUCKET: str = os.getenv('STAMPY_BUCKET', 'stampy-nlp-resources')
DUPLICATES_FILENAME: str = os.getenv('DUPLICATES_FILENAME', 'stampy-duplicates.json')
AUTH_PASSWORD: str = os.getenv('AUTH_PASSWORD', 'miko')

def get_coda_token():
    if CODA_TOKEN is None:
        raise Exception("Missing environment variable CODA_TOKEN")
    return CODA_TOKEN


def get_huggingface_key():
    if not HUGGINGFACE_API_KEY:
        raise Exception("Missing environment variable HUGGINGFACE_API_KEY")
    return HUGGINGFACE_API_KEY


def get_pinecode_key():
    if PINECONE_API_KEY is None:
        raise Exception("Missing environment variable PINECONE_API_KEY")
    return PINECONE_API_KEY
