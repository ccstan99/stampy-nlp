import os
from dotenv import load_dotenv


load_dotenv()


LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

CODA_TOKEN: str = os.getenv('CODA_TOKEN')
PINECONE_API_KEY: str = os.getenv('PINECONE_API_KEY')
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')

STAMPY_BUCKET: str = os.getenv('STAMPY_BUCKET', 'stampy-nlp-resources')
DUPLICATES_FILENAME: str = os.getenv('DUPLICATES_FILENAME', 'stampy-duplicates.json')
AUTH_PASSWORD: str = os.getenv('AUTH_PASSWORD')

QA_MODEL_URL: str = os.getenv('QA_MODEL_URL')
RETRIEVER_MODEL_URL: str = os.getenv('RETRIEVER_MODEL_URL')
LIT_SEARCH_MODEL_URL: str = os.getenv('LIT_SEARCH_MODEL_URL')

ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS')
if ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS.split(',')]
else:
    ALLOWED_ORIGINS = '*'


def check_required_vars():
    required_vars = {
        'CODA_TOKEN': CODA_TOKEN,
        'PINECONE_API_KEY': PINECONE_API_KEY,
        'OPENAI_API_KEY': OPENAI_API_KEY,
    }
    missing_vars = [var_name for var_name, val in required_vars.items() if not val]
    if missing_vars:
        raise Exception(f"Missing environment variables: {', '.join(missing_vars)}")


def get_coda_token():
    return CODA_TOKEN


def get_pinecode_key():
    return PINECONE_API_KEY


def get_openai_key():
    return OPENAI_API_KEY
