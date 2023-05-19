import pandas as pd
import numpy as np
import jsonlines
from urllib.parse import urlparse

COUNT = 5
PATH = '/mnt/c/Users/euryd/PycharmProjects/data/'
IN_FILE = 'alignment_texts.jsonl'
OUT_FILE = 'alignment_texts_cleaned.jsonl'

""" 
Reformat dataset so each entry has: id, source, title, summary, text, url.
Remove stampy content which will be fetched fresh internally.
"""
def clean_alignment_texts():
    quality_sources = ['aipulse', 'cold-takes', 'qualiacomputing', 'deepmindsafetyresearch', 'aiimpacts.org', 'vkrakovna', 'jsteinhardt', 'intelligence.org', 'aisafety.camp', 'yudkowsky']
    large_sources = ['lesswrong', 'alignment forum', 'arxiv']
    skip_sources = ['cold-takes', 'ebook']
    # quality_sources = ['alignment forum']
    data_list = []
    num_errors = 0
    count = 0
    with jsonlines.open(PATH + IN_FILE, "r") as f:
        for item in f:
            count += 1
            # if count > 3000:
            #     break
            try:
                keys = item.keys()
                source = item['source'] if 'source' in keys else ''

                # if source in quality_sources:
                if 'printouts' not in keys and source not in large_sources:
                    text = item['text']
                    id = str(hash(text))
                    title = item['title'] if 'title' in keys else ''
                    url = item['url'] if 'url' in keys else item['links'] if 'links' in keys else item['link'] if 'link' in keys else ''
                    if isinstance(url, list):
                        if 'href' in url[0].keys():
                            url = url[0]['href']

                    source = urlparse(url).netloc if len(source) == 0 else source
                    for name in quality_sources:
                        if name in source:
                            source = name

                    data_list.append({
                        'id': id,
                        'source': source,
                        'url': url,
                        'title': title,
                        # 'summary': '',
                        # 'text': '',
                    })
            except KeyError as err:
                print("ERROR:", err, item['text'][:100])
                num_errors += 1
                pass

    with jsonlines.open(PATH + OUT_FILE, "w") as f:
        for item in data_list:
            f.write(item)

    print('\n***\nnum_errors', num_errors)
    return data_list

data = clean_alignment_texts()
