import os
from dotenv import load_dotenv


load_dotenv()


CODA_TOKEN: str = os.getenv('CODA_TOKEN')
HUGGINGFACE_API_KEY: str = os.getenv('HUGGINGFACE_API_KEY')
PINECONE_API_KEY: str = os.getenv('PINECONE_API_KEY')

STAMPY_BUCKET: str = os.getenv('STAMPY_BUCKET', 'stampy-nlp-resources')
DUPLICATES_FILENAME: str = os.getenv('DUPLICATES_FILENAME', 'stampy-duplicates.json')
AUTH_PASSWORD: str = os.getenv('AUTH_PASSWORD')


required_vars = {
    'CODA_TOKEN': CODA_TOKEN,
    'HUGGINGFACE_API_KEY': HUGGINGFACE_API_KEY,
    'PINECONE_API_KEY': PINECONE_API_KEY,
}
missing_vars = [var_name for var_name, val in required_vars.items() if not val]
if missing_vars:
    raise Exception(f"Missing environment variables: {', '.join(missing_vars)}")


def get_coda_token():
    return CODA_TOKEN


def get_huggingface_key():
    return HUGGINGFACE_API_KEY


def get_pinecode_key():
    return PINECONE_API_KEY
