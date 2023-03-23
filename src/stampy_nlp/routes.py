import logging
import requests
from functools import wraps
from flask import render_template, jsonify, request, Blueprint
from stampy_nlp.settings import AUTH_PASSWORD
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK
from stampy_nlp.faq_titles import encode_faq_titles
from stampy_nlp.search import semantic_search, extract_qa, lit_search

logger = logging.getLogger(__name__, )
logger.setLevel(logging.DEBUG)

DEFAULT_QUERY: str = 'What is AI Safety?'
DUPLICATES_URL: str = 'https://storage.googleapis.com/stampy-nlp-resources/stampy-duplicates.json'


def show_duplicates():
    return requests.get(DUPLICATES_URL).json()


def as_bool(name, default='false'):
    return request.args.get(name, default).lower() in ['1', 'true']


def as_int(name, default=None):
    try:
        return int(request.args.get(name))
    except (TypeError, ValueError):
        return default


def check_auth(username, password):
    return AUTH_PASSWORD and username == 'stampy' and password == AUTH_PASSWORD


def auth_required(f):
    @wraps(f)
    def wrapped_view(**kwargs):
        auth = request.authorization
        if not (auth and check_auth(auth.username, auth.password)):
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })

        return f(**kwargs)

    return wrapped_view


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
@auth_required
def encode_faq_api():
    logger.debug('encode_faq_api()')
    return encode_faq_titles()


@api.route('/search', methods=['GET'])
def search_api():
    logger.debug('search_api()')
    query = request.args.get('query', DEFAULT_QUERY)
    top_k = as_int('top', DEFAULT_TOPK)
    status = request.args.getlist('status')
    show_live = as_bool('showLive', 'true')

    return jsonify(semantic_search(query, top_k=top_k, showLive=show_live, status=status))


@api.route('/duplicates', methods=['GET'])
def duplicates_api():
    logger.debug('api_duplicates()')
    return jsonify(show_duplicates())


@api.route('/literature', methods=['GET'])
def literature_api():
    logger.debug('literature_api()')
    query = request.args.get("query", DEFAULT_QUERY)
    top_k = as_int("top", DEFAULT_TOPK)
    return jsonify(lit_search(query, top_k=top_k))


@api.route('/extract', methods=['GET', 'POST'])
def extract_api():
    logger.debug('extract_api()')
    if request.method == "POST":
        query = request.form.query
    elif request.method == "GET":
        query = request.args.get("query", DEFAULT_QUERY)
    return jsonify(extract_qa(query))
