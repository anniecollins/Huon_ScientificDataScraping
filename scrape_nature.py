import json
import pandas as pd
import os
from dotenv import load_dotenv
from urllib.request import urlopen, Request
import xmltodict
import tqdm
import numpy as np


def load_api_key():
    load_dotenv()
    return os.getenv('NATURE_API_KEY')


def fetch_data(query_url):
    req = Request(query_url)
    file = urlopen(req)
    data = file.read()
    file.close()
    return xmltodict.parse(data)


def parse_article(article_data):
    this_article = pd.DataFrame()

    # Info about article/journal
    journal_meta = article_data['front']['journal-meta']
    article_meta = article_data['front']['article-meta']
    this_article['journalName'] = [journal_meta['journal-title-group']['journal-title']]

    journal_id = journal_meta['journal-id']
    this_article['journalId'] = [journal_id[0]['#text'] if isinstance(journal_id, list) else journal_id['#text']]
    this_article['doi'] = [article_meta['article-id'][-1]['#text']]
    this_article['url'] = ["https://doi.org/"+article_meta['article-id'][-1]['#text']]
    this_article['title'] = [article_meta['title-group']['article-title']['#text']] if '#text' in article_meta['title-group']['article-title'].keys() else [None]

    if isinstance(article_meta['pub-date'], dict):
        pub_date = article_meta['pub-date']
    else:
        pub_date = article_meta['pub-date'][0]
    this_article['pubDay'] = int(pub_date['day'])
    this_article['pubMonth'] = int(pub_date['month'])
    this_article['pubYear'] = int(pub_date['year'])

    # I think some articles are not open access so we don't have the back section
    if 'back' not in article_data.keys():
        return this_article

    back_sec = article_data['back'].get('sec', [])
    if isinstance(back_sec, dict):
        back_sec = [back_sec]

    for sec in back_sec:
        if sec.get('@sec-type') == "data-availability":

            ext_link = None
            code_text = [None]
            if 'p' in sec.keys():
                if isinstance(sec['p'], dict):
                    ext_link = sec['p'].get('ext-link')
                    code_text = [sec['p'].get('#text', None)] # else [sec['p']] if isinstance(sec['p'], str) else [str(sec['p'])] if isinstance(sec['p'], list) else [None]
                elif isinstance(sec['p'], str):
                    code_text = [sec['p']]
                elif isinstance(sec['p'], list):
                    code_text = [str(sec['p'])]
            if isinstance(ext_link, dict):
                this_article['codeLink'] = [ext_link.get('#text', None)]
            elif isinstance(ext_link, list):
                this_article['codeLink'] = ["; ".join([link['#text'] for link in ext_link])]

            this_article['codeText'] = code_text
    return this_article


def main():
    API_KEY = load_api_key()
    base = "https://api.springernature.com/"
    endpoint = "openaccess/jats"

    articles = pd.DataFrame()

    for i in tqdm.tqdm(np.arange(1, 12000, 100)):  # There are 1239 articles
        query = f"?q=(python%20OR%20github)%20year:2023%20sort:date&p=100&s={i}&api_key={API_KEY}"
        url = base + endpoint + query

        data = fetch_data(url)

        for article in data['response']['records']['article']:
            this_article = parse_article(article)
            articles = pd.concat([articles, this_article], axis=0)

    articles['pubDate'] = pd.to_datetime(articles[['pubDay', "pubMonth", "pubYear"]].rename(columns={'pubDay': "day", 'pubMonth': "month", 'pubYear': "year"}))
    articles.to_csv(os.path.join("data", "nature_articles.csv"))


if __name__ == "__main__":
    main()
