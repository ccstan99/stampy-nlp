import pytest
import pandas as pd
from unittest.mock import patch, Mock
from stampy_nlp.faq_titles import find_duplicates, encode_faq_titles, MODEL_ID
from sentence_transformers import SentenceTransformer, util


@pytest.fixture
def mock_pinecone_upload():
    with patch('stampy_nlp.faq_titles.upload_data') as mock:
        yield mock


def test_find_duplicates():
    model = SentenceTransformer(MODEL_ID)
    titles = [
        # These shouldn't have duplicates
        'This is a unique title',
        'My name is randomness, destroyer of worlds',
        'In the beginning, God created the heavens and th earth',

        # Obvious duplicates
        'This one is about cats',
        'Cats is the topic of this one',

        # Less obvious duplicates
        'What are cows?',
        'An inquiry into the nature of bovines',

        # Triplicates
        'A story about dr Who',
        'This tells the tale of dr Who',
        'The adventures of dr Who',
    ]

    data = [(title, f'http://bla.bla?title={title}') for title in titles]
    data = pd.DataFrame(data, columns=['title', 'url'])
    with patch('stampy_nlp.faq_titles.save_duplicates'):
        dups = find_duplicates(model, data)
        confident_duplicate_pairs = [
            (i['entry1']['title'], i['entry2']['title'])
            for i in dups if i['score'] > 0.5
        ]
        assert confident_duplicate_pairs == [
            ('A story about dr Who', 'This tells the tale of dr Who'),
            ('This tells the tale of dr Who', 'The adventures of dr Who'),
            ('A story about dr Who', 'The adventures of dr Who'),

            ('This one is about cats', 'Cats is the topic of this one'),

            ('What are cows?', 'An inquiry into the nature of bovines')
        ]


def test_find_duplicates_limit():
    """Check that only the first MAX_DUPLICATES are returned."""
    model = SentenceTransformer(MODEL_ID)
    titles = [
        'This is a duplicate title',
    ] * 200

    data = [(title, f'http://bla.bla?title={title}') for title in titles]
    data = pd.DataFrame(data, columns=['title', 'url'])
    with patch('stampy_nlp.faq_titles.save_duplicates'):
        with patch('stampy_nlp.faq_titles.MAX_DUPLICATES', 5):
            dups = find_duplicates(model, data)

    confident_duplicate_pairs = [
        (i['entry1']['title'], i['entry2']['title'])
        for i in dups if i['score'] > 0.5
    ]
    print(confident_duplicate_pairs)
    assert confident_duplicate_pairs == [('This is a duplicate title', 'This is a duplicate title')] * 5
