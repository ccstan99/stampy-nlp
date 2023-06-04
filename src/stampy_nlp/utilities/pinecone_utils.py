"""Pinecone Vector DB Functions

Write to Pinecone vector database for finding nearest embedding.
"""
import pinecone
import logging
from stampy_nlp.settings import get_pinecode_key


DEFAULT_TOPK: int = 5
DIMS: int = 768
GCP_ENV: str = 'us-west1-gcp'
PINECONE_INDEX: str = 'alignment-lit'
PINECONE_NAMESPACE: str = 'faq-titles'


def init_db():
    """Initialize pinecone vector database to find nearest embeddings"""
    logging.debug("init_db")

    pinecone.init(api_key=get_pinecode_key(), environment=GCP_ENV)
    if PINECONE_INDEX not in pinecone.list_indexes():
        pinecone.create_index(name=PINECONE_INDEX, dimension=DIMS)
    index = pinecone.Index(PINECONE_INDEX)

    return index


INDEX = None
def get_index():
    global INDEX
    if INDEX is None:
        INDEX = init_db()
    return INDEX


def upload_data(ids, vectors, meta, namespace: str = PINECONE_NAMESPACE, delete_all: bool = False):
    """Upload embeddings to pinecone vector database for faster query"""
    logging.debug("upload_data()")
    index = get_index()
    if delete_all:
        index.delete(delete_all=True, namespace=PINECONE_NAMESPACE)

    # upload in smaller batches to avoid errors
    batch_size = 100
    length = len(ids)
    logging.info(f"upload_data {length}")
    for i in range(0, length, batch_size):
        logging.info(f"upsert: {PINECONE_NAMESPACE} {i} {i+batch_size}")
        index.upsert(
            list(zip(ids[i:i+batch_size],
                 vectors[i:i+batch_size], meta[i:i+batch_size])),
            namespace=namespace
        )
