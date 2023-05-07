from unittest.mock import patch, Mock
import requests
import pytest
from stampy_nlp.settings import ALLOWED_ORIGINS
from data.duplicates import STAMPY_DUPLICATES


@pytest.mark.parametrize('origin', ALLOWED_ORIGINS)
def test_cors(client, origin):
    response = client.get('/api/log_query', headers={'Origin': origin})
    assert response.headers.get('Access-Control-Allow-Origin') == origin


@pytest.mark.skipif(ALLOWED_ORIGINS == '*', reason='CORS is not being used')
def test_cors_non_whitelisted(client):
    # Note: This test depends on the value of the `ALLOWED_ORIGINS` env variable. If this test
    # is failing and you have no idea why, check there
    response = client.get('/api/log_query', headers={'Origin': 'http://this.probably.wont.ever.be.whitelisted'})
    assert 'Access-Control-Allow-Origin' not in response.headers


def test_duplicates(client, stampy_duplicates):
    response = client.get('/api/duplicates')
    assert response.status_code == 200
    assert response.json == STAMPY_DUPLICATES


@pytest.mark.parametrize('name, caller_type, query', (
    # All values provided
    ('GET', '/api/bla', 'ble ble ble'),
    ('POST', '/api/blee', 'bla bla bla'),
    ('function_call', 'write_query', 'who am I?'),

    # Empty values will still be used
    ('', '/api/bla', 'ble ble ble'),
    ('GET', '', 'ble ble ble'),
    ('GET', '/api/bla', ''),

    # Only some values provided
    (None, '/api/bla', 'ble ble ble'),
    ('GET', None, 'ble ble ble'),
    ('GET', '/api/bla', None),
    (None, None, None)

))
def test_log_query_endpoint(client, name, caller_type, query):
    params = {
        'name': name,
        'type': caller_type,
        'query': query,
    }
    query_string = '&'.join(
        f'{param}={value}' for param, value in params.items()
        if value is not None
    )

    logger = Mock()
    with patch('stampy_nlp.logger.make_logger', return_value=logger):
        response = client.get('/api/log_query?' + query_string)
        logger.info.assert_called_once_with('%s %s: %s', caller_type, name, query)

    assert response.status_code == 200


SEARCH_ENDPOINT = 'https://nlp.stampy.ai/api/search'

@pytest.mark.live
def test_search_known_question():
    response = requests.get(SEARCH_ENDPOINT, params={'query': 'What is AI safety?', 'showLive': 1})
    questions = response.json()
    assert questions
    assert 'What is AI safety?' in [i['title'] for i in questions]
    assert {i['status'] for i in questions} == {'Live on site'}


@pytest.mark.live
def test_search_known_question_live():
    response = requests.get(SEARCH_ENDPOINT, params={'query': 'What is AI safety?', 'showLive': 0})
    questions = response.json()
    assert questions
    assert 'Live on site' not in {i['status'] for i in questions}


@pytest.mark.live
def test_search_all():
    response = requests.get(SEARCH_ENDPOINT, params={'query': 'Something random', 'top': 20, 'status': 'all'})
    questions = response.json()
    assert len(questions) == 20

    statuses = {i['status'] for i in questions}
    # This is a potential cause of Heisenbugs, seeing as it's possible that the top 20
    # questions returned are all live. But this isn't all that likely, so should be fine...?
    assert len(statuses) > 1
    assert 'Live on site' in statuses


@pytest.mark.live
def test_search_specific_status():
    response = requests.get(
        SEARCH_ENDPOINT,
        params={'query': 'Something random', 'top': 20, 'status': ['Not started', 'In progress']}
    )
    questions = response.json()
    assert len(questions) == 20

    # This is a potential cause of Heisenbugs, seeing as it's possible that the top 20
    # questions returned are all live. But this isn't all that likely, so should be fine...?
    assert {i['status'] for i in questions} == {'Not started', 'In progress'}
