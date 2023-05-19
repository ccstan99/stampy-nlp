import logging
import json
import sys
from google.cloud import storage
from sentence_transformers import SentenceTransformer, util
from stampy_nlp.settings import STAMPY_BUCKET, DUPLICATES_FILENAME
from stampy_nlp.utilities.pinecone_utils import upload_data, DEFAULT_TOPK
import stampy_nlp.utilities.coda_utils as codautils

logger = logging.getLogger(__name__)


MODEL_ID: str = 'multi-qa-mpnet-base-cos-v1'
COUNT: int = 3
MAX_DUPLICATES:int = 100
delete_all: bool = False


def extract_details(df_row):
    """Extract relevant columns given dataframe row"""
    return {
        'title': df_row['title'],
        'url': df_row['url']
    }


def upload_duplicates(duplicates):
    client = storage.Client()
    bucket = client.get_bucket(STAMPY_BUCKET)
    blob = bucket.blob(DUPLICATES_FILENAME)
    logger.info('Uploading duplicates to %s', blob.public_url)
    blob.upload_from_string(json.dumps(duplicates))


def find_duplicates(model, data):
    """Use SentenceTransformer util.paraphrase to find duplicates"""
    logging.debug(f"find_duplicates()")
    titles = data['title']
    mined = util.paraphrase_mining(model, titles, show_progress_bar=True)
    duplicates = list(map(lambda x: {
        'score': x[0],
        'entry1': extract_details(data.iloc[x[1]]),
        'entry2': extract_details(data.iloc[x[2]])
    }, mined))
    duplicates = duplicates[:MAX_DUPLICATES]
    with open('stampy-duplicates.json', 'w') as f:
        json.dump(duplicates, f)
    # upload_duplicates(duplicates)
    return duplicates


def encode_faq_titles():
    """Pull FAQ from Coda, embed titles, find duplicates, then store in Pinecone DB"""
    try:
        data = codautils.get_df_data()
        logger.debug("data.index %s", data.index[:COUNT])
    except Exception as e:
        logger.error('Failed get_df_data() reading from Coda.')
        raise(e)
    
    try:
        model = SentenceTransformer(MODEL_ID)
        logger.debug("Initializing SentenceTransformer model %s", MODEL_ID)
    except Exception as e:
        logger.error("Failed initializing model")
        raise(e)

    try:
        duplicates = find_duplicates(model, data)
        logger.debug("find_duplicates %s", duplicates[:COUNT])
    except Exception as e:
        logger.error("Failed find_duplicates")
        raise(e)

    try:
        embeddings = model.encode(data['title']).tolist()
        metadata = json.loads(data.to_json(orient='records'))
        logger.debug("metadata %s", metadata[:COUNT])
    except Exception as e:
        logger.error("Failed embed_text")
        raise(e)

    try:
        upload_data(data.index.tolist(), embeddings, metadata, delete_all=delete_all)
    except Exception as e:
        logger.error("Failed upload_data to pinecone")
        raise(e)
    
    return duplicates


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) > 1 and sys.argv[1] == '-delete-all':
        logger.debug("sys.argv[1]=%s", sys.argv[1])
        delete_all = True
    logger.debug("delete_all=%s", delete_all)

    encode_faq_titles()
