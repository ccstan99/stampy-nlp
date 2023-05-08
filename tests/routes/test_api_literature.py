from unittest.mock import patch
import requests
import pytest


pytestmark = pytest.mark.unstable


def test_literature_api_defaults(client, mock_lit_search):
    response = client.get('/api/literature')
    assert response.status_code == 200
    assert [i['title'] for i in response.json] == [
        'Safe AI -- How is this Possible?',
        'Unpredictability of AI',
        'Understanding and Avoiding AI Failures: A Practical Guide',
        'The Concept of Criticality in AI Safety',
        'System Safety and Artificial Intelligence'
    ]


def test_literature_api_query_required(client):
    response = client.get('/api/literature', query_string={'query': ''})
    assert response.status_code == 400
    assert response.json == {'error': 'No query provided'}


def test_literature_query_logged(client, mock_lit_search):
    with patch('stampy_nlp.routes.log_query') as logger:
        response = client.get(f'/api/literature?query=Find me some data')
        logger.assert_called_once_with('/api/literature', 'GET', 'Find me some data')

    assert response.status_code == 200


def test_literature_query_logged_default(client, mock_lit_search):
    with patch('stampy_nlp.routes.log_query') as logger:
        response = client.get(f'/api/literature')
        logger.assert_called_once_with('/api/literature', 'GET', 'What is AI Safety?')

    assert response.status_code == 200


@pytest.mark.parametrize('query, first_item', (
    ('What is AI Safety?', 'Safe AI -- How is this Possible?'),
    ('Find me some data', 'Adam: A Method for Stochastic Optimization'),
))
def test_literature_api_query(client, mock_lit_search, query, first_item):
    response = client.get(f'/api/literature?query={query}')
    assert response.status_code == 200
    assert response.json[0]['title'] == first_item


@pytest.mark.parametrize('top', (1, 2, 5, 10))
def test_literature_api_top(client, mock_lit_search, top):
    response = client.get(f'/api/literature?top={top}')
    assert response.status_code == 200
    assert len(response.json) == top


@pytest.mark.parametrize('top', (None, '', 'bla', 'all'))
def test_literature_api_invalid_top(client, mock_lit_search, top):
    """Invalid `top` params will result in 5 items being returned."""
    response = client.get(f'/api/literature?top={top}')
    assert response.status_code == 200
    assert len(response.json) == 5


SEARCH_ENDPOINT = 'https://nlp.stampy.ai/api/literature'

@pytest.mark.live
def test_search_known_question():
    response = requests.get(SEARCH_ENDPOINT, params={'query': 'What is AI Safety?', 'top': 20})
    assert response.ok
    questions = response.json()
    assert len(questions) == 20
    assert questions[0].keys() == {'abstract', 'authors', 'id', 'score', 'title', 'url'}
