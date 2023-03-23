import logging
import os
import json
import requests


if AUTH_PASSWORD := os.getenv('AUTH_PASSWORD') is None:
    raise Exception("Missing environment variable AUTH_PASSWORD")

NLP_API_URL: str = 'https://stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles'
# NLP_API_URL: str = 'https://test---stampy-nlp-t6p37v2uia-uw.a.run.app/api/encode-faq-titles'
# NLP_API_URL: str = 'http://localhost:8080/api/encode-faq-titles'
FILENAME: str = 'stampy-duplicates.json'
MAX: int = 100


def encode_faq_titles():
    """Call NLP API to encode Coda question then upload to Pinecone"""
    logging.debug("encode_faq_titles()")
    print("NLP_API_URL", NLP_API_URL)
    duplicates = requests.post(NLP_API_URL, auth=('stampy', AUTH_PASSWORD)).json()
    with open(FILENAME, 'w') as f:
        json.dump(duplicates[:MAX], f)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    encode_faq_titles()
