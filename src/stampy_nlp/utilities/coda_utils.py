"""Cdoa Utilies

Pull AI Safety FAQs from Coda
"""
import pandas as pd
import logging
import requests
from typing import List

from stampy_nlp.settings import get_coda_token


CODA_DOC_ID: str = 'fau7sl2hmG'
TABLE_ID: str = 'table-YvPEyAXl8a'
LIVE_STATUS: str = 'Live on site'
EXCLUDE_STATUS: List[str] = ['Duplicate', 'Marked for deletion']
TABLE_URL: str = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{TABLE_ID}/rows'


UI_ID_COLUMN = 'c-203KwSC2N_'
RICH_TEXT_COLUMN = 'c-a82d-vxRc9'


def fetch_all_rows():
    headers: object = {'Authorization': f'Bearer {get_coda_token()}'}
    params: object = {
        'useColumnNames': True,
        'limit': 10000
    }
    response = requests.get(TABLE_URL, headers=headers, params=params).json()
    while response:
        for item in response['items']:
            yield item
        next_page = response.get('nextPageLink')
        response = next_page and requests.get(next_page, headers=headers).json()


def get_df_data(is_similar = lambda n1, n2: n1 == n2, delete_all: bool = False):
    """Fetches questions from Coda and returns a pandas dataframe for processing"""
    logging.debug("get_df_data()")

    data_list = []
    similar_alternates = []
    for item in fetch_all_rows():
        values = item['values']
        pageid = str(values['UI ID']).strip()
        status = values['Status']
        names = [item['name']]
        # add alternate phrasings only if db already populated, else is_similar always false
        if not delete_all:
            names = [val for val in values.get('All Phrasings', '').split('\n') if val] or [item['name']]

        # link to UI if available else use coda link
        if status == 'Live on site':
            url = 'https://aisafety.info?state=' + pageid
        else:
            url = values['Link']

        # add to data_list if some kinds of question, even if unanswered
        if len(pageid) >= 4 and status not in EXCLUDE_STATUS:
            for i, name in enumerate(names):
                if i > 0 and is_similar(item['name'], name):
                    logging.info('Skipping similar alternate phrasing: %s (%s)\t%s', pageid, item['name'], name)
                    similar_alternates.append({
                        'pageid': pageid, 
                        'original question':item['name'], 
                        'alternate phrasing':name
                    })
                    continue
                data_list.append({
                    # ids must be unique, and the first name is the original name, which means that
                    # any subsequent names are duplicates
                    'id': f'{item["id"]}{i or ""}',
                    'title': name,
                    'status': status,
                    'pageid': pageid,
                    'url': url,
                })

    df_similar = pd.DataFrame(similar_alternates)
    df_similar.to_csv("similar_alternates.tsv", sep='\t', index=False)
    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    return df


def get_row(ui_id):
    headers: object = {'Authorization': f'Bearer {get_coda_token()}'}
    params: object = {
        'useColumnNames': True,
    }
    response = requests.get(TABLE_URL, headers=headers, params={'query': f'{UI_ID_COLUMN}:"{ui_id}"'}).json()
    if items := response.get('items'):
        return items[0]
    return None


def get_contents(ui_id):
    contents = get_row(ui_id)
    return contents and contents['values'][RICH_TEXT_COLUMN]
