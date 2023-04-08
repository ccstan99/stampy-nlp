import requests

from stampy_nlp.settings import (
    QA_MODEL_URL, LIT_SEARCH_MODEL_URL, RETRIEVER_MODEL_URL,
)
from stampy_nlp.logger import make_logger
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK, get_index


logger = make_logger(__name__)


class ModelConnectionError(Exception):
    pass


class Model:
    def __init__(self, host, model_name, pinecone=None):
        self.host = host
        self.pinecone = pinecone
        self.model_name = model_name

    def _post(self, endpoint, payload):
        resp = requests.post(self.host + endpoint, json=payload)
        if not resp.status_code == 200:
            raise ModelConnectionError(
                f'Could not run model: status={resp.status_code}, contents={resp.text}'
            )
        return resp.json()

    def connect_pinecone(self, pinecone):
        self.pinecone = pinecone

    def encode(self, query):
        return self._post('/encoding', {'query': query})

    def search(self, query, namespace, top_k=DEFAULT_TOPK, includeMetadata=True, **kwargs):
        xq = self.encode(query)
        logger.debug('%s - model encode: %s', self.model_name, xq[:3])
        results = self.pinecone.query(
            xq, namespace=namespace,
            top_k=top_k, includeMetadata=includeMetadata,
            **kwargs
        )
        logger.debug('%s - fetched results from pinecone', self.model_name)
        return results

    def paraphrase_mining(self, titles):
        return self._post('/paraphrase_mining', {'titles': titles})

    def question_answering(self, question, context):
        return self._post('/question_answering', {'query': question, 'context': context})


qa_model = Model(QA_MODEL_URL, 'qa_model')
retriever_model = Model(RETRIEVER_MODEL_URL, 'retriever')
lit_search_model = Model(LIT_SEARCH_MODEL_URL, 'lit_search')


def connect_pinecone(pinecone):
    qa_model.connect_pinecone(pinecone)
    retriever_model.connect_pinecone(pinecone)
    lit_search_model.connect_pinecone(pinecone)
