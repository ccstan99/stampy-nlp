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
def mock_retriever_model():
    def get_retriever_encodings(query):
        """The models return a massive list of embeddings to be sent directly to Pinecone.
        Seeing as thay're not modified, sending a different string should be fine..."""
        encoder = Mock()
        encoder.tolist.return_value = query
        return encoder

    model = Mock(encode=get_retriever_encodings)

    def get_pinecode_results(xq, namespace, filter, top_k, *args, **kwargs):
        """There are a load of Pinecone results saved as json results, so just read from the appropriate one."""
        with open(Path(__file__).parent / (f'data/pinecone/{xq}+{namespace}+{filter}+{top_k}.json')) as f:
            data = json.load(f)

        matches = [
            Mock(id=item['id'], score=item['score'], metadata=item)
            for item in data
        ]
        return {'matches': matches}

    with patch('stampy_nlp.search.get_retriever', return_value=model):
        with patch('stampy_nlp.search.query_db', get_pinecode_results):
            yield
