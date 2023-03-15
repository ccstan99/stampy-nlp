import requests
import pytest
from data.duplicates import STAMPY_DUPLICATES


def test_duplicates(client, stampy_duplicates):
    response = client.get('/api/duplicates')
    assert response.status_code == 200
    assert response.json == STAMPY_DUPLICATES


def test_search_defaults(client, mock_retriever_model):
    response = client.get('/api/search')
    assert response.status_code == 200
    assert response.json == [
        {
            'id': 'i-8899afafb469e7a7e3691f2b506fec68b4567eb11d991ce0f21e99ad1527f4ee',
            'pageid': '8486', 'score': 1.0, 'status': 'Live on site', 'title': 'What is AI safety?',
            'url': 'https://aisafety.info?state=8486'
        }, {
            'id': 'i-fafba101539a91083ec9b47e64aad4224f5fc28456e76227738cd60a552f7682',
            'pageid': '6297', 'score': 0.781057715, 'status': 'Live on site',
            'title': 'Why is safety important for smarter-than-human AI?',
            'url': 'https://aisafety.info?state=6297'
        }, {
            'id': 'i-ab8afa359ddffc0d30a562d66b228e2b520b71b468c9a89c031af91f447bd074',
            'pageid': '87O6', 'score': 0.768612862, 'status': 'Live on site',
            'title': 'What are some arguments for AI safety being less important?',
            'url': 'https://aisafety.info?state=87O6'
        }, {
            'id': 'i-7a91fe76021bd1ef050520611a26a0525b161f08855c6e80b901d06c0ec8535b',
            'pageid': '86J8', 'score': 0.756911337, 'status': 'Live on site',
            'title': 'What are some introductions to AI safety?',
            'url': 'https://aisafety.info?state=86J8'
        }, {
            'id': 'i-45bfa544bf341cc543f8dec3b6700e8105a08d5c4c80698f8607290af71366b9',
            'pageid': '8201', 'score': 0.753655732, 'status': 'Live on site',
            'title': 'What is AI Safety via Debate?', 'url': 'https://aisafety.info?state=8201'
        }
    ]


def test_search_query(client, mock_retriever_model):
    response = client.get('/api/search?query=Find me some data')
    assert response.status_code == 200
    assert response.json == [
        {
            'id': 'i-03dd33916b47a6a7b02e6ae2fc2c761daef93b29006605e08dea3bb9f54510c3',
            'pageid': '7487', 'score': 0.290963888, 'status': 'Live on site',
            'title': 'What sources of information can Stampy use?', 'url': 'https://aisafety.info?state=7487'
        }, {
            'id': 'i-23986d44d356f98e9cbeeaa57a50156aa7d2c20533921d6e720027ecb79d8c2a',
            'pageid': '85E0', 'score': 0.245712325, 'status': 'Live on site',
            'title': 'What are some exercises and projects I can try?', 'url': 'https://aisafety.info?state=85E0'
        }, {
            'id': 'i-448ea6cca773bc70178351c8f0677b2dcaea0ccac1c7c9864f10ae45d1305a47', 'pageid': '8509',
            'score': 0.171540141, 'status': 'Live on site', 'url': 'https://aisafety.info?state=8509',
            'title': 'What links are especially valuable to share on social media or other contexts?',
        }, {
            'id': 'i-1d5eb8d5c0cf35af3e3950adab08e484ef6db52aea4363237fcabb6649961548',
            'pageid': '6300', 'score': 0.160711259, 'status': 'Live on site',
            'url': 'https://aisafety.info?state=6300',
            'title': 'What technical problems are MIRI working on?',
        }, {
            'id': 'i-2d01b4830ba4fc500f89ed9b319fc2acafadfa7a3f07db4b733be9e4cac801f3',
            'pageid': '7844', 'score': 0.159782887, 'status': 'Live on site',
            'title': 'What are some specific open tasks on Stampy?', 'url': 'https://aisafety.info?state=7844'
        }
    ]


@pytest.mark.parametrize('top_k', [1, 2, 5, 10])
def test_search_limit_results(client, mock_retriever_model, top_k):
    response = client.get(f'/api/search?top={top_k}')
    assert response.status_code == 200
    assert len(response.json) == top_k


@pytest.mark.parametrize('status, expected_statuses', (
    (['all'], {'Not started', 'In progress', 'Live on site'}),
    (['all', 'Live on site'], {'Not started', 'In progress', 'Live on site'}),
    (['In review'], {'In review'}),
    (['In progress', 'In review'], {'In progress', 'In review'}),
))
def test_search_filter_status(client, mock_retriever_model, status, expected_statuses):
    status_string = '&'.join(f'status={s}' for s in status)
    response = client.get('/api/search?top=10&' + status_string)
    assert response.status_code == 200
    assert {i['status'] for i in response.json} == expected_statuses


@pytest.mark.parametrize('showLive', ('true', 'TrUe', '1'))
def test_search_showLive_selected(client, mock_retriever_model, showLive):
    response = client.get(f'/api/search?top=10&showLive={showLive}')
    assert response.status_code == 200
    assert {i['status'] for i in response.json} == {'Live on site'}


@pytest.mark.parametrize('showLive', ('0', 'no', 'false', 'bla', 'asdadsa'))
def test_search_showLive_disabled(client, mock_retriever_model, showLive):
    response = client.get(f'/api/search?top=10&showLive={showLive}')
    assert response.status_code == 200
    assert {i['status'] for i in response.json} == {'In progress', 'Not started'}


def test_search_status_overrides_showLive(client, mock_retriever_model):
    response = client.get(f'/api/search?top=10&showLive=true&status=In review')
    assert response.status_code == 200
    assert {i['status'] for i in response.json} == {'In review'}


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
