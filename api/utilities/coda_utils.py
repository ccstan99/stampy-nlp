"""Cdoa Utilies 

Pull AI Safety FAQs from Coda
"""
import pandas as pd
import logging
import os
import requests


CODA_DOC_ID: str = 'fau7sl2hmG'
TABLE_ID: str = 'Answers'
LIVE_STATUS: str = 'Live on site'


def get_df_data():
    """Fetches questions from Coda and returns a pandas dataframe for processing"""
    logging.debug(f"get_df_data()")
    CODA_TOKEN: str = os.getenv('CODA_TOKEN')
    if (CODA_TOKEN == None):
        raise Exception("Missing environment variable CODA_TOKEN")

    url: str = f'https://coda.io/apis/v1/docs/{CODA_DOC_ID}/tables/{TABLE_ID}/rows'
    headers: object = {'Authorization': f'Bearer {CODA_TOKEN}'}
    params: object = {
        'useColumnNames': True,
        'limit': 1000
    }
    json_items = requests.get(url, headers=headers,
                              params=params).json()['items']
    data_list = []
    for item in json_items:
        values = item['values']
        pageid = str(values['UI ID']).strip()
        status = values['Status']

        # link to UI if available else use coda link
        if status == 'Live on site':
            url = 'https://aisafety.info?state=' + pageid
        else:
            url = values['Link']

        # add to data_list if some kinds of question, even if unanswered
        if isinstance(pageid, str) and len(pageid) >= 4:
            data_list.append({
                'id': item['id'],
                'title': item['name'],
                'status': status,
                'pageid': pageid,
                'url': url,
            })

    df = pd.DataFrame(data_list)
    df.set_index('id', inplace=True)
    return df
