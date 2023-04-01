import json
from unittest.mock import patch, Mock
from pathlib import Path
import pytest
from stampy_nlp.main import make_app
from data.duplicates import STAMPY_DUPLICATES

@pytest.fixture
def app():
    with patch('stampy_nlp.main.check_required_vars'):
        with patch('stampy_nlp.main.get_index', return_value=Mock()):
            app = make_app()
    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def stampy_duplicates():
    with patch('stampy_nlp.routes.show_duplicates', return_value=STAMPY_DUPLICATES):
        yield


def clean_name(name, disallowed_chars='<>:"/\|?*'):
    for c in disallowed_chars:
        name = name.replace(c, 'X')
    return name.strip().rstrip('.')


def get_pinecode_results(xq, namespace, top_k=None, filter=None, **kwargs):
    """There are a load of Pinecone results saved as json results, so just read from the appropriate one."""
    filename = clean_name(f'{xq}+{namespace}+{filter}+{top_k}.json')
    with open(Path(__file__).parent / 'data' / 'pinecone' / filename) as f:
        data = json.load(f)

    matches = [
        Mock(id=item['id'], score=item.get('score'), metadata=item.get('metadata', item), __getitem__=getattr)
        for item in data
    ]
    return {'matches': matches}


@pytest.fixture
def mock_retriever_model():
    model = Mock(
        encode=lambda query: query,
        search=get_pinecode_results,
    )
    with patch('stampy_nlp.search.retriever_model', model):
        yield


@pytest.fixture
def mock_qa_model():
    def get_reader_encodings(question, context):
        filename = clean_name(f'{question}+{context[:20]}.json')
        with open(Path(__file__).parent / 'data' / 'semantic_search' / 'reader' / filename) as f:
            return json.load(f)

    with patch('stampy_nlp.search.qa_model.question_answering', get_reader_encodings):
        yield


@pytest.fixture
def mock_lit_search():
    model = Mock(
        encode=lambda query: query,
        search=get_pinecode_results,
    )
    with patch('stampy_nlp.search.lit_search_model', model):
        yield


# Add a command to run live tests - this will by default skip tests marked as live
def pytest_addoption(parser):
    parser.addoption(
        "--rununstable", action="store_true", default=False, help="run tests for parts of the code that are unstable"
    )
    parser.addoption(
        "--runlive", action="store_true", default=False, help="run live tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "unstable: mark test for code that is liable to change often")
    config.addinivalue_line("markers", "live: mark test as running on production")


def pytest_collection_modifyitems(config, items):
    should_run_live = config.getoption("--runlive")
    skip_live = pytest.mark.skip(reason="need --runlive option to run")

    should_run_unstable = config.getoption("--rununstable")
    skip_unstable = pytest.mark.skip(reason="need --rununstable option to run")

    for item in items:
        if "live" in item.keywords and not should_run_live:
            item.add_marker(skip_live)
        elif "unstable" in item.keywords and not should_run_unstable:
            item.add_marker(skip_unstable)
