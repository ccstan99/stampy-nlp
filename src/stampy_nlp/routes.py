import logging
import requests
from flask import render_template, jsonify, request, Blueprint
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK
from stampy_nlp.faq_titles import encode_faq_titles
from stampy_nlp.search import semantic_search, extract_qa, lit_search

logger = logging.getLogger(__name__, )
logger.setLevel(logging.DEBUG)

DEFAULT_QUERY: str = 'What is AI Safety?'
DUPLICATES_URL: str = 'https://storage.googleapis.com/stampy-nlp-resources/stampy-duplicates.json'


def show_duplicates():
    return requests.get(DUPLICATES_URL).json()


frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def search_html():
    logger.debug('search_html()')
    query = DEFAULT_QUERY
    return render_template('search.html', query=query, results=semantic_search(query))


@frontend.route('/duplicates')
def duplicates_html():
    logger.debug('duplicates_html()')
    return render_template('duplicates.html', results=show_duplicates())


@frontend.route('/literature')
def literature_html():
    logger.debug('literature_html()')
    query = DEFAULT_QUERY
    return render_template("literature.html", query=query, results=lit_search(query))


@frontend.route('/extract')
def extract_html():
    logger.debug('extract_html()')
    query = DEFAULT_QUERY
    return render_template('extract.html', query=query, results=extract_qa(query))


api = Blueprint('api', __name__)

@api.route('/encode-faq-titles', methods=['POST'])
def encode_faq_api():
    logger.debug('encode_faq_api()')
    return encode_faq_titles()


@api.route('/search', methods=['GET'])
def search_api():
    logger.debug('search_api()')
    query = request.args.get('query', DEFAULT_QUERY)
    top_k = request.args.get('top', DEFAULT_TOPK)
    status = request.args.getlist('status')
    showLive = request.args.get('showLive', 'true').lower() in ['1', 'true']
    try:
        top_k = int(top_k)
    except ValueError:
        top_k = DEFAULT_TOPK
    return jsonify(semantic_search(query, top_k=top_k, showLive=showLive, status=status))


@api.route('/duplicates', methods=['GET'])
def duplicates_api():
    logger.debug('api_duplicates()')
    return jsonify(show_duplicates())


@api.route('/literature', methods=['GET'])
def literature_api():
    logger.debug('literature_api()')
    query = request.args.get("query", DEFAULT_QUERY)
    top_k = request.args.get("top", DEFAULT_TOPK)
    try:
        top_k = int(top_k)
    except ValueError:
        top_k = DEFAULT_TOPK
    return jsonify(lit_search(query, top_k=top_k))


@api.route('/extract', methods=['GET'])
def extract_api():
    logger.debug('extract_api()')
    if request.method == "POST":
        query = request.form.query
    if request.method == "GET":
        query = request.args.get("query", DEFAULT_QUERY)
    return jsonify(extract_qa(query))
