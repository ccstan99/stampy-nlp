import requests

from stampy_nlp.settings import (
    QA_MODEL_URL, LIT_SEARCH_MODEL_URL, RETRIEVER_MODEL_URL,
)
from stampy_nlp.logger import make_logger
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK, get_index

logger = make_logger(__name__)


class ModelConnectionError(Exception):
    pass


class BaseModel:
    def __init__(self, model_name, pinecone=None):
        self.pinecone = pinecone
        self.model_name = model_name

    def connect_pinecone(self, pinecone):
        self.pinecone = pinecone

    def encode(self, query):
        raise NotImplementedError

    def search(self, query, namespace, top_k=DEFAULT_TOPK, includeMetadata=True, **kwargs):
        xq = self.encode(query)
        logger.debug('%s - model encode: %s', self.model_name, xq[:3])

        # Questions can have alternative phrasings, which can result in duplicates being returned.
        # Pinecone doesn't seem to have a nice way of aggregating answers, so this is done here manually.
        # This will involve removing duplicates, so to keep the number of returned items around `top_k`,
        # more items will be fetched. It's assumed that there won't be more than ~50% of duplicates
        results = self.pinecone.query(
            xq, namespace=namespace,
            top_k=int(top_k*1.5), includeMetadata=includeMetadata,
            **kwargs
        )

        logger.debug('%s - fetched results from pinecone', self.model_name)

        # Replace the matches with the first `top_k` results, removing duplicates
        items = {}
        for result in results['matches']:
            pageid = result['metadata']['pageid']
            if pageid not in items:
                items[pageid] = result
        results['matches'] = list(items.values())[:top_k]

        return results

    def paraphrase_mining(self, titles):
        raise NotImplementedError

    def question_answering(self, question, context):
        raise NotImplementedError


class HttpModel(BaseModel):
    def __init__(self, host, model_name, pinecone=None):
        super().__init__(model_name, pinecone)
        self.host = host

    def _post(self, endpoint, payload):
        resp = requests.post(self.host + endpoint, json=payload)
        if not resp.status_code == 200:
            raise ModelConnectionError(
                f'Could not run model: status={resp.status_code}, contents={resp.text}'
            )
        return resp.json()

    def encode(self, query):
        return self._post('/encoding', {'query': query})

    def paraphrase_mining(self, titles):
        return self._post('/paraphrase_mining', {'titles': titles})

    def question_answering(self, question, context):
        return self._post('/question_answering', {'query': question, 'context': context})


# Handle people wanting to run models locally.
try:
    from sentence_transformers import SentenceTransformer, util

    class SentenceTransformerModel(BaseModel):
        def __init__(self, model_path, model_name, pinecone=None):
            super().__init__(model_name, pinecone)
            logger.info('Using local sentence transformer model for %s', model_name)
            self.model = SentenceTransformer(model_path)

        def encode(self, query):
            return self.model.encode(query).tolist()

        def paraphrase_mining(self, titles):
            return util.paraphrase_mining(self.model, titles, show_progress_bar=True)

    logger.info('Loaded local model')
except ModuleNotFoundError:
    SentenceTransformerModel = BaseModel


def make_model(model_uri, name):
    if not model_uri:
        return BaseModel(name)
    if not model_uri.strip().startswith('http'):
        return SentenceTransformerModel(model_uri, name)
    return HttpModel(model_uri, name)


qa_model = make_model(QA_MODEL_URL, 'qa_model')
retriever_model = make_model(RETRIEVER_MODEL_URL, 'retriever')
lit_search_model = make_model(LIT_SEARCH_MODEL_URL, 'lit_search')


def connect_pinecone(pinecone):
    qa_model.connect_pinecone(pinecone)
    retriever_model.connect_pinecone(pinecone)
    lit_search_model.connect_pinecone(pinecone)
