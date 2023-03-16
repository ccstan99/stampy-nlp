import json
from unittest.mock import patch, Mock
from pathlib import Path
import pytest
from stampy_nlp.main import make_app
from stampy_nlp.utilities.huggingface_utils import get_retriever
from data.duplicates import STAMPY_DUPLICATES

@pytest.fixture
def app():
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


@pytest.fixture
def mock_pinecone_search():
    def get_pinecode_results(xq, namespace, top_k=None, filter=None, **kwargs):
        """There are a load of Pinecone results saved as json results, so just read from the appropriate one."""
        filename = f'data/pinecone/{xq}+{namespace}+{filter}+{top_k}.json'
        with open(Path(__file__).parent / filename) as f:
            data = json.load(f)

        matches = [
            Mock(id=item['id'], score=item.get('score'), metadata=item.get('metadata', item), __getitem__=getattr)
            for item in data
        ]
        return {'matches': matches}

    with patch('stampy_nlp.search.query_db', get_pinecode_results):
        yield


@pytest.fixture
def mock_retriever_model(mock_pinecone_search):
    def get_retriever_encodings(query):
        """The models return a massive list of embeddings to be sent directly to Pinecone.
        Seeing as thay're not modified, sending a different string should be fine..."""
        encoder = Mock()
        encoder.tolist.return_value = query
        return encoder

    model = Mock(encode=get_retriever_encodings)

    with patch('stampy_nlp.search.get_retriever', return_value=model):
        yield


@pytest.fixture
def mock_reader_model(mock_pinecone_search):
    def get_reader_encodings(question, context):
        filename = f'data/semantic_search/reader/{question}+{context[:20]}.json'
        with open(Path(__file__).parent / filename) as f:
            return json.load(f)

    with patch('stampy_nlp.search.get_reader', return_value=get_reader_encodings):
        yield


@pytest.fixture
def mock_huggingface_search(mock_pinecone_search):
    with patch('stampy_nlp.search.hf_search', lambda query: query):
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
