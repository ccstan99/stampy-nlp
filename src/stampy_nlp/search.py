import logging
import urllib
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK, query as query_db
from stampy_nlp.utilities.huggingface_utils import get_reader, get_retriever, lit_search as hf_search
from stampy_nlp.utilities.coda_utils import LIVE_STATUS
from stampy_nlp.faq_titles import encode_faq_titles

logger = logging.getLogger(__name__, )
logger.setLevel(logging.DEBUG)

COUNT: int = 3
DEFAULT_QUERY: str = 'What is AI Safety?'
BLANK: str = ''
ALL: str = 'all'


def format_matches(results):
    results_list = []
    for item in results['matches']:
        result = {k: v for (k, v) in item.metadata.items()}
        result['id'] = item.id
        result['score'] = item.score
        logger.debug("result %s", result)
        results_list.append(result)

    return results_list


def semantic_search(query: str, top_k: int = DEFAULT_TOPK, showLive: bool = True, status=[], namespace: str = 'faq-titles'):
    """Semantic search for query"""
    logger.info("semantic_search: %s", query)
    logger.debug("params top_k=%s, status=%s, showLive=%s", top_k, status, showLive)
    xq = get_retriever().encode(query).tolist()
    logger.debug('model encode: %s', xq[:COUNT])
    filters = {}
    if not status:
        if showLive:
            filters = {'status': LIVE_STATUS}
        else:
            filters = {'status': {'$ne': LIVE_STATUS}}
    elif ALL not in status:
        filters = {'status': {'$in': status}}

    results = query_db(xq, namespace=namespace, filter=filters, top_k=top_k, includeMetadata=True)
    return format_matches(results)


def lit_search(query, top_k=DEFAULT_TOPK, namespace='paper-abstracts'):
    """Search index of arxiv paper abstracts and blog post summaries"""
    logger.debug("lit_search (%s, %s)", query, top_k)
    # lit search expect lower freq, use HF http inference API for now
    xq = hf_search(query)
    logger.debug("model encode: %s", xq[:5])
    results = query_db(xq, namespace=namespace, top_k=top_k, includeMetadata=True)
    return format_matches(results)


def extract_answer(query, item):
    metadata = item['metadata']
    logger.debug("result: (%s, %s)", item.id, item.score)
    context = str(metadata['text'])
    logger.debug("context: %s", context)

    response = get_reader()(question=query, context=context)
    logger.debug("response: %s", response)
    try:
        score = response['score']
        answer = response['answer']
        logger.debug("score: %s", score)
        return {
            'id': item.id,
            'score': score,
            'title': str(metadata['title']),
            'url': str(metadata['url']) + "#:~:text=" + urllib.parse.quote(answer),
            'context': str(metadata['text']),
            'start': response['start'],
            'end': response['end'],
            'answer': answer,
        }
    except KeyError:
        pass


def extract_qa(query, namespace='extracted-chunks'):
    """Search extracted chunks alignment dataset"""
    logger.debug("extract_qa:{query}")
    xq = get_retriever().encode(query).tolist()
    logger.debug("model encode: %s", xq[:5])
    results = query_db(xq, namespace=namespace, top_k=10, includeMetadata=True)

    answers = {}
    for item in results['matches']:
        answer = extract_answer(query, item)
        if answer['score'] > 0.001:
            answers[answer['id']] = answer

    return sorted(answers.values(), key=lambda x: x['score'], reverse=True)
