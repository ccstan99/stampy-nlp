import urllib
from stampy_nlp.utilities.openai_utils import generate_answer
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK
from stampy_nlp.logger import make_logger
from stampy_nlp.utilities.coda_utils import LIVE_STATUS
from stampy_nlp.faq_titles import encode_faq_titles
from stampy_nlp.models import qa_model, retriever_model, lit_search_model

logger = make_logger(__name__)

COUNT: int = 3
DEFAULT_QUERY: str = 'What is AI Safety?'
BLANK: str = ''
ALL: str = 'all'
NONBLANK_URL = {'url': {'$ne': BLANK}}


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
    logger.debug("params top_k=%s, status=%s, showLive=%s",
                 top_k, status, showLive)
    filters = {}
    if not status:
        if showLive:
            filters = {'status': LIVE_STATUS}
        else:
            filters = {'status': {'$ne': LIVE_STATUS}}
    elif ALL not in status:
        filters = {'status': {'$in': status}}

    results = retriever_model.search(
        query, namespace=namespace, filter=filters, top_k=top_k)
    return format_matches(results)


def lit_search(query, top_k=DEFAULT_TOPK, namespace='paper-abstracts'):
    """Search index of arxiv paper abstracts and blog post summaries"""
    logger.debug("lit_search (%s, %s)", query, top_k)
    results = lit_search_model.search(query, namespace=namespace, top_k=top_k)
    return format_matches(results)


def extract_answer(query, item):
    metadata = item['metadata']
    logger.debug("result: (%s, %s)", item.id, item.score)
    context = str(metadata['text'])
    logger.debug("context: %s", context)

    response = qa_model.question_answering(query, context)
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


def extract_qa(query, namespace: str = 'extracted-chunks'):
    """Search extracted chunks alignment dataset"""
    logger.debug("extract_qa:{query}")
    results = retriever_model.search(query, namespace=namespace, top_k=10)

    answers = {}
    for item in results['matches']:
        answer = extract_answer(query, item)
        if answer['score'] > 0.001:
            answers[answer['id']] = answer

    return sorted(answers.values(), key=lambda x: x['score'], reverse=True)


def generate_qa(query, namespace: str = 'extracted-chunks', top_k: int = DEFAULT_TOPK, **kwargs):
    """Search extracted chunks alignment dataset. ChatGPT generates answer based on sources"""
    logger.info("generate_qa: %s", query)
    logger.debug("params top_k=%s, namespace=%s", top_k, namespace)

    results = retriever_model.search(query, namespace=namespace, top_k=top_k, filter=NONBLANK_URL)
    sources = []
    source_content = ''
    for item in results["matches"]:
        if item["score"] > 0.3:
            source_content += "\n\nLINK: " + item["metadata"]["url"]
            source_content += "\n\nCONTENT: " + item["metadata"]["text"]
            logger.debug("item score: %f %s %s",
                         item["score"], item["metadata"]["title"], item["metadata"]["url"])
            if item["metadata"]["url"]:
                sources.append({'url': item["metadata"]["url"], 'title': item["metadata"]["title"]})

    sources = sorted(sources, key=lambda i: 'aisafety.info' not in i['url'])
    generated_text = generate_answer(query, source_content, **kwargs)
    logger.debug("return generated_text=%s", generated_text)
    logger.debug("return source_content=%s", source_content)

    return {"generated_text": generated_text, "sources": sources}
