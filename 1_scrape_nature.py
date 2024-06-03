import json
import pandas as pd
import os
from dotenv import load_dotenv
from urllib.request import urlopen, Request
import xmltodict
import tqdm
import numpy as np

load_dotenv()

API_KEY = os.getenv('API_KEY')
base = "https://api.springernature.com/"
endpoint = "openaccess/jats"

articles = pd.DataFrame()

for i in tqdm.tqdm(np.arange(1, 1239, 100)): # There are 1239 articles on
    query = f"?q=python%20journalid:41597%20sort:date&p=100&s={i}&api_key="

    url = base + endpoint + query + API_KEY
    req = Request(url)

    # For metadata
    # data = json.load(urlopen(req))

    # For full text
    file = urlopen(req)
    data = file.read()
    file.close()
    data = xmltodict.parse(data)

    for j in range(len(data['response']['records']['article'])):
        this_article = pd.DataFrame()

        # Info about article/journal
        this_article['journalName'] = [data['response']['records']['article'][j]['front']['journal-meta']['journal-title-group']['journal-title']]
        this_article['journalId'] = [data['response']['records']['article'][j]['front']['journal-meta']['journal-id'][0]['#text'] if isinstance(data['response']['records']['article'][j]['front']['journal-meta']['journal-id'], list) else data['response']['records']['article'][j]['front']['journal-meta']['journal-id']['#text']]
        this_article['doi'] = [data['response']['records']['article'][j]['front']['article-meta']['article-id'][-1]['#text']]
        this_article['title'] = [data['response']['records']['article'][j]['front']['article-meta']['title-group']['article-title']['#text']]
        this_article['pubDay'] = int(data['response']['records']['article'][j]['front']['article-meta']['pub-date'][0]['day'])
        this_article['pubMonth'] = int(data['response']['records']['article'][j]['front']['article-meta']['pub-date'][0]['month'])
        this_article['pubYear'] = int(data['response']['records']['article'][j]['front']['article-meta']['pub-date'][0]['year'])

        if 'sec' in data['response']['records']['article'][j]['back'].keys():
            back_sec = data['response']['records']['article'][j]['back']['sec']
        else:
            continue

        # Work around to make sure `back_sec` is iterable
        if isinstance(back_sec, dict):
            back_sec = [back_sec]

        for sec in back_sec:
            if '@sec-type' in sec.keys() and sec['@sec-type'] == "data-availability":
                # need ['ext-link']['@xlink:href'] and ['#text']
                if isinstance(sec['p'], dict) and "ext-link" in sec['p'].keys():
                    if isinstance(sec['p']['ext-link'], dict):
                        this_article['codeLink'] = [sec['p']['ext-link']['#text']] if 'ext-link' in sec['p'].keys() else [None]
                    elif isinstance(sec['p']['ext-link'], list):
                        this_article['codeLink'] = "; ".join([link['#text'] for link in sec['p']['ext-link']])
                    this_article['codeText'] = [sec['p']['#text']] if '#text' in sec['p'].keys() else [None]
                elif isinstance(sec['p'], str):
                    this_article['codeText'] = [sec['p']]
                elif isinstance(sec['p'], list):
                    this_article['codeMisc'] = [str(sec['p'])]

        articles = pd.concat([articles, this_article], axis=0)

articles['pubDate'] = pd.to_datetime(articles[['pubDay', "pubMonth", "pubYear"]].rename(columns={'pubDay': "day", 'pubMonth': "month", 'pubYear': "year"}))

articles.to_csv(os.path.join("data", "data/scientific_data_articles.csv"))


