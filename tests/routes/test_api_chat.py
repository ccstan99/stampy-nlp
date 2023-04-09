from unittest.mock import patch
import requests
import pytest


pytestmark = pytest.mark.unstable


def test_chat_api_defaults(client, mock_retriever_model):
    with patch('stampy_nlp.search.generate_answer', return_value="This is a generated answer"):
        response = client.get('/api/chat')
    assert response.status_code == 200
    assert response.json == {
        'generated_text': 'This is a generated answer',
        'sources': [
            {
                'title': 'Title of doc 4',
                'url': 'https://aisafety.info/?state=9991_'
            },
            {
                'title': 'Title of doc 1',
                'url': 'https://www.lesswrong.com/posts/Fu7bqAyCMjfcMzBah/3109021'
            },
            {
                'title': 'Title of doc 2',
                'url': 'https://arxiv.org/abs/1890.61439'
            }
        ]
    }


@pytest.mark.parametrize('data', (
    {},
    {'namespace': 'extracted_chunks'},
    {'top_k': 4},
    {'max_history': 200},
    {'constrain': True},

    {'namespace': 'extracted_chunks', 'top_k': 4, 'max_history': 200, 'constrain': True},
))
def test_chat_api_params_parsed_GET(client, data):
    with patch('stampy_nlp.routes.generate_qa', return_value={}) as generate_qa:
        client.get('/api/chat', query_string=data)
        generate_qa.assert_called_once_with('What is AI Safety?', **data)


@pytest.mark.parametrize('data', (
    {},
    {'namespace': 'extracted_chunks'},
    {'top_k': 4},
    {'max_history': 200},
    {'constrain': True},

    {'namespace': 'extracted_chunks', 'top_k': 4, 'max_history': 200, 'constrain': True},
))
def test_chat_api_params_parsed_POST(client, data):
    with patch('stampy_nlp.routes.generate_qa', return_value={}) as generate_qa:
        client.post(f'/api/chat', data=data)
        generate_qa.assert_called_once_with('What is AI Safety?', **data)


@pytest.mark.parametrize('data, expected', (
    ({}, {}),
    ({'blaaa': 'bleeee'}, {}),
    ({'namespace': 'extracted_chunks', 'ble': 'ble'}, {'namespace': 'extracted_chunks'}),
))
def test_chat_api_params_parsed_ignore_unknown(client, data, expected):
    with patch('stampy_nlp.routes.generate_qa', return_value={}) as generate_qa:
        client.get('/api/chat', query_string=data)
        generate_qa.assert_called_once_with('What is AI Safety?', **expected)
