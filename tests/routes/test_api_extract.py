from unittest.mock import patch
import requests
import pytest


pytestmark = pytest.mark.unstable


def test_extract_api_defaults(client, mock_retriever_model, mock_qa_model):
    response = client.get('/api/extract')
    assert response.status_code == 200
    assert [i['answer'] for i in response.json] == [
        'smarter-than-human AI',
        'the project of spreading it',
        'a relatively new field of research focused on techniques for building AI beneficial for humans',
        'to avoid catastrophic outcomes from advanced AI',
        'studies how to prevent human-harming accidents when deploying AI systems',
        'paradigm safe',
        'software-based automation in safety-critical domains',
        'first AGIs will be built by humans',
    ]


def test_extract_api_query_required(client):
    response = client.get('/api/extract', query_string={'query': ''})
    assert response.status_code == 400
    assert response.json == {'error': 'No query provided'}


def test_extract_api_score(client, mock_retriever_model, mock_qa_model):
    response = client.get('/api/extract')
    assert response.status_code == 200
    assert all(i['score'] > 0.001 for i in response.json)


def test_extract_query_logged(client, mock_retriever_model, mock_qa_model):
    with patch('stampy_nlp.routes.log_query') as logger:
        response = client.get(f'/api/extract?query=Find me some data')
        logger.assert_called_once_with('/api/extract', 'GET', 'Find me some data')

    assert response.status_code == 200


def test_extract_query_logged_default(client, mock_retriever_model, mock_qa_model):
    with patch('stampy_nlp.routes.log_query') as logger:
        response = client.get(f'/api/extract')
        logger.assert_called_once_with('/api/extract', 'GET', 'What is AI Safety?')

    assert response.status_code == 200


@pytest.mark.parametrize('question, expected_first', (
    ('What is AI Safety?', 'smarter-than-human AI'),
    ('Find me some data', 'extensive data about individual users across a long period of time')
))
def test_extract_api_question(client, mock_retriever_model, mock_qa_model, question, expected_first):
    response = client.get(f'/api/extract?query={question}')
    assert response.status_code == 200
    assert response.json[0]['answer'] == expected_first


SEARCH_ENDPOINT = 'https://nlp.stampy.ai/api/extract'

@pytest.mark.live
def test_extract_api_live():
    response = requests.get(SEARCH_ENDPOINT, params={'query': 'What is AI safety?'})
    assert response.ok
    answers = response.json()
    assert len(answers) >= 5
    assert answers[0].keys() == {'answer', 'context', 'end', 'id', 'score', 'start', 'title', 'url'}
