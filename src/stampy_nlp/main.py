import logging
import requests
import urllib
from flask import Flask, render_template, jsonify, request
import stampy_nlp.utilities.pinecone_utils as dbutils
import stampy_nlp.utilities.huggingface_utils as hfutils
import stampy_nlp.utilities.coda_utils as codautils
from stampy_nlp.faq_titles import encode_faq_titles

app = Flask(__name__)

COUNT: int = 3
DEFAULT_TOPK: int = dbutils.DEFAULT_TOPK
DEFAULT_QUERY: str = 'What is AI Safety?'
BLANK: str = ''
TRUE: str = 'True'
ALL: str = 'all'
LIVE_STATUS: str = codautils.LIVE_STATUS
DUPLICATES_URL: str = 'https://storage.googleapis.com/stampy-nlp-resources/stampy-duplicates.json'


def semantic_search(query: str, top_k: int = DEFAULT_TOPK, showLive: bool = True, status=[], namespace: str = 'faq-titles'):
    """Semantic search for query"""
    logging.info(f"semantic_search: {query}")
    logging.debug(f"params top_k={top_k}, status={status}, showLive={showLive}")
    # xq = RETRIEVER_MODEL(query)[0][0]
    xq = RETRIEVER_MODEL.encode(query).tolist()
    logging.debug('model encode:', xq[:COUNT])
    filter = {}
    if status == []:
        if showLive:
            filter = {'status': LIVE_STATUS}
        else:
            filter = {'status': {'$ne': LIVE_STATUS}}
    elif ALL not in status:
        filter = {'status': {'$in': status}}

    results = db_index.query(xq, namespace=namespace,
                             filter=filter, top_k=top_k, includeMetadata=True)
    results_list = []
    for item in results['matches']:
        result = {k: v for (k, v) in item.metadata.items()}
        result['id'] = item.id
        result['score'] = item.score
        logging.debug(f"result {result}")
        results_list.append(result)
    return results_list


def lit_search(query, top_k=DEFAULT_TOPK, namespace='paper-abstracts'):
    """Search index of arxiv paper abstracts and blog post summaries"""
    logging.debug(f"lit_search ({query}, {top_k}")
    # lit search expect lower freq, use HF http inference API for now
    xq = hfutils.lit_search(query)
    # xq = LIT_MODEL.encode(query).tolist()
    logging.debug(f"model encode: {xq[:5]}")
    results = db_index.query(xq, namespace=namespace,
                             top_k=top_k, includeMetadata=True)
    results_list = []
    for item in results['matches']:
        result = {k: v for (k, v) in item.metadata.items()}
        result['id'] = item.id
        result['score'] = item.score
        logging.debug(f"result {result}")
        results_list.append(result)
    return results_list


def extract_qa(query, namespace='extracted-chunks'):
    """Search extracted chunks alignment dataset"""
    logging.debug("extract_qa:{query}")
    xq = RETRIEVER_MODEL.encode(query).tolist()
    logging.debug(f"model encode: {xq[:5]}")
    results = db_index.query(xq, namespace=namespace,
                             top_k=10, includeMetadata=True)
    results_list = []

    for item in results['matches']:
        metadata = item['metadata']
        logging.debug(f"result: {item.id} {item.score}")
        context = str(metadata['text'])
        logging.debug(f"context:{context}")

        response = READER_MODEL(question=query, context=context)
        logging.debug(f"response: {response}")
        try:
            score = response['score']
            answer = response['answer']
            logging.debug(f"score: {score}")
            if score > 0.001:
                results_list.append({
                    'id': item.id,
                    'score': score,
                    'title': str(metadata['title']),
                    'url': str(metadata['url']) + "#:~:text=" + urllib.parse.quote(answer),
                    'context': str(metadata['text']),
                    'start': response['start'],
                    'end': response['end'],
                    'answer': answer,
                })
        except KeyError:
            pass
        # TODO: remove duplicate docs
        results_list = sorted(
            results_list, key=lambda x: x['score'], reverse=True)

    return results_list


def show_duplicates():
    return requests.get(DUPLICATES_URL).json()


db_index = dbutils.init_db()
RETRIEVER_MODEL = hfutils.init_retriever()
READER_MODEL = hfutils.init_reader()


@app.route('/')
def search_html():
    logging.debug('search_html()')
    query = DEFAULT_QUERY
    return render_template('search.html', query=query, results=semantic_search(query))


@app.route('/duplicates')
def duplicates_html():
    logging.debug('duplicates_html()')
    return render_template('duplicates.html', results=show_duplicates())


@app.route('/literature')
def literature_html():
    logging.debug('literature_html()')
    query = DEFAULT_QUERY
    return render_template("literature.html", query=query, results=lit_search(query))


@app.route('/extract')
def extract_html():
    logging.debug('extract_html()')
    query = DEFAULT_QUERY
    return render_template('extract.html', query=query, results=extract_qa(query))


@app.route('/api/encode-faq-titles', methods=['POST'])
def encode_faq_api():
    logging.debug('encode_faq_api()')
    return encode_faq_titles()

@app.route('/api/search', methods=['GET'])
def search_api():
    logging.debug('search_api()')
    query = request.args.get('query', DEFAULT_QUERY)
    top_k = request.args.get('top', DEFAULT_TOPK)
    status = request.args.getlist('status')
    showLive = eval(request.args.get('showLive', TRUE))
    try:
        top_k = int(top_k)
    except ValueError:
        top_k = DEFAULT_TOPK
    return jsonify(semantic_search(query, top_k=top_k, showLive=showLive, status=status))


@app.route('/api/duplicates', methods=['GET'])
def duplicates_api():
    logging.debug('api_duplicates()')
    return show_duplicates()


@app.route('/api/literature', methods=['GET'])
def literature_api():
    logging.debug('literature_api()')
    query = request.args.get("query", DEFAULT_QUERY)
    top_k = request.args.get("top", DEFAULT_TOPK)
    try:
        top_k = int(top_k)
    except ValueError:
        top_k = DEFAULT_TOPK
    return jsonify(lit_search(query, top_k=top_k))


@app.route('/api/extract', methods=['GET'])
def extract_api():
    logging.debug('extract_api()')
    if request.method == "POST":
        query = request.form.query
    if request.method == "GET":
        query = request.args.get("query", DEFAULT_QUERY)
    return jsonify(extract_qa(query))


def run():
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=8080)


if __name__ == '__main__':
    run()
