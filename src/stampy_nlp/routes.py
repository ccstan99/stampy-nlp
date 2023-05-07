import logging
import requests
from functools import wraps
from flask import render_template, jsonify, request, Blueprint
from stampy_nlp.settings import AUTH_PASSWORD
from stampy_nlp.logger import make_logger, log_query
from stampy_nlp.utilities.pinecone_utils import DEFAULT_TOPK
from stampy_nlp.faq_titles import encode_faq_titles
from stampy_nlp.search import semantic_search, lit_search, extract_qa, generate_qa, DEFAULT_QUERY

logger = make_logger(__name__)

DUPLICATES_URL: str = 'https://storage.googleapis.com/stampy-nlp-resources/stampy-duplicates.json'


def show_duplicates():
    return requests.get(DUPLICATES_URL).json()


def as_bool(name, default='false', source=None):
    source = source or request.args
    return source.get(name, default).lower() in ['1', 'true']


def as_int(name, default=None, source=None):
    source = source or request.args
    try:
        return int(source.get(name))
    except (TypeError, ValueError):
        return default


def check_auth(username, password):
    return AUTH_PASSWORD and username == 'stampy' and password == AUTH_PASSWORD


def get_query(request):
    if request.method == 'GET':
        query = request.args.get('query', DEFAULT_QUERY)
    elif request.method == 'POST':
        query = request.form.get('query', DEFAULT_QUERY)
    else:
        query = None
    return query


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


def log_queries(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        query = get_query(request)
        log_query(request.path, request.method, query)
        return f(*args, **kwargs)
    return wrapper


def require_query(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        query = get_query(request)
        if not (query and query.strip()):
            return {'error': 'No query provided'}, 400
        return f(*args, **kwargs)
    return wrapper


frontend = Blueprint('frontend', __name__, template_folder='templates')

@frontend.route('/')
@log_queries
def search_html():
    logger.debug('search_html()')
    query = DEFAULT_QUERY
    return render_template('search.html', query=query, results=semantic_search(query))


@frontend.route('/duplicates')
def duplicates_html():
    logger.debug('duplicates_html()')
    return render_template('duplicates.html', results=show_duplicates())


@frontend.route('/literature')
@log_queries
def literature_html():
    logger.debug('literature_html()')
    query = DEFAULT_QUERY
    return render_template("literature.html", query=query, results=lit_search(query))


@frontend.route('/extract')
@log_queries
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
@require_query
@log_queries
def search_api():
    logger.debug('search_api()')
    query = request.args.get('query', DEFAULT_QUERY)
    top_k = as_int('top', DEFAULT_TOPK)
    status = request.args.getlist('status')
    show_live = as_bool('showLive', 'true')

    return jsonify(semantic_search(query, top_k=top_k, showLive=show_live, status=status))


@api.route('/duplicates', methods=['GET'])
def duplicates_api():
    logger.debug('duplicates_api()')
    return jsonify(show_duplicates())


@api.route('/literature', methods=['GET'])
@require_query
@log_queries
def literature_api():
    logger.debug('literature_api()')
    query = request.args.get("query", DEFAULT_QUERY)
    top_k = as_int("top", DEFAULT_TOPK)
    return jsonify(lit_search(query, top_k=top_k))


@api.route('/chat', methods=['GET', 'POST'])
@require_query
@log_queries
def chat_api():
    logger.debug('chat_api()')
    if request.method == "POST":
        data = request.form
    elif request.method == "GET":
        data = request.args

    query = data.get('query', DEFAULT_QUERY)
    params = {}
    if namespace := data.get('namespace'):
        params['namespace'] = namespace
    if top_k := as_int('top_k', 0, data):
        params['top_k'] = top_k
    if max_history := as_int('max_history', 0, data):
        params['max_history'] = max_history
    if constrain := as_bool('constrain', 'false', data):
        params['constrain'] = constrain

    return jsonify(generate_qa(query, **params))


@api.route('/extract', methods=['GET', 'POST'])
@require_query
@log_queries
def extract_api():
    logger.debug('extract_api()')
    if request.method == "POST":
        query = request.form.query
    elif request.method == "GET":
        query = request.args.get("query", DEFAULT_QUERY)
    return jsonify(extract_qa(query))


@api.route('/log_query', methods=['GET'])
def log_query_endpoint():
    logger.debug('log_query()')
    log_query(
        request.args.get("name"),
        request.args.get("type"),
        request.args.get("query"),
    )
    return jsonify({'result': 'ok'})
