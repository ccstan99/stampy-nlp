import logging
import requests
import os
import json

CODA_TOKEN: str = os.getenv('CODA_TOKEN')
if CODA_TOKEN is None:
    raise Exception("Missing environment variable CODA_TOKEN")
AUTH_PASSWORD = os.getenv('AUTH_PASSWORD', 'miko')

NLP_API_HDR: object = {'Authorization': f'Bearer { "CODA_TOKEN" }'}
NLP_API_JSON: object = { }
NLP_API_URL: str = 'https://stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles'
# NLP_API_URL: str = 'https://test---stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles'
# NLP_API_URL: str = 'http://localhost:8080/api/encode-faq-titles'
FILENAME: str = 'stampy-duplicates.json'
MAX: int = 100


def encode_faq_titles():
    """Call NLP API to encode Coda question then upload to Pinecone"""
    logging.debug("encode_faq_titles()")
    print("NLP_API_URL", NLP_API_URL)
    duplicates = requests.post(
        NLP_API_URL, headers=NLP_API_HDR, json=NLP_API_JSON, auth=('stampy', AUTH_PASSWORD)
    ).json()
    with open(FILENAME, 'w') as f:
        json.dump(duplicates[:MAX], f)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    encode_faq_titles()
