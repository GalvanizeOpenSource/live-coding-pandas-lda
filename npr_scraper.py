import pandas as pd
import numpy as np
import requests
from sys import argv
import os
import json

# Import NPR API Access key from zsh profile
API_KEY = os.environ['NPR_ACCESS_KEY']

def get_dates(start_date, end_date):
    ''' Returns a list of dates in 'YYYY-MM-DD' format

    Parameters
    -----------
    start_date - str
        string in 'YYYY-MM-DD' or 'YYYY-M-DD' format
    end_date - str
        string in 'YYYY-MM-DD' or 'YYYY-M-DD' format

    Returns
    --------
    list of date strings at a daily frequency
    '''
    date_range = pd.date_range(start_date, end_date, freq='D')
    date_range = [date.strftime('%Y-%m-%d') for date in date_range]
    return date_range


def single_query(date, start_num=0):
    payload = {
        'fields': 'all',
        'requiredAssets': 'text',
        'date': date,
        'startNum': start_num,
        'dateType': 'story',
        'output': 'JSON',
        'numResults': 20,
        'searchType': 'fullContent',
        'apiKey': API_KEY
    }
    url = 'http://api.npr.org/query'
    response = requests.get(url, params=payload)
    if response.status_code != 200:
        print('WARNING', response.status_code)
    else:
        return response.json()


def extract_info(article):
    '''
    INPUT: dict object with output from the api
    OUTPUT: bool if extraction was successful or not,
            dict object to insert into mongodb
    '''
    headline = article['title']['$text']
    date_published = str(article['pubDate']['$text'])
    try:
        author = [str(author['name']['$text']) for author in article['byline']]
    except:
        author = None
    try:
        url = str(article['link'][0]['$text'])
    except:
        return False
    try:
        article_text = ' '.join([line.get('$text', '\n') for line in article['text']['paragraph']])
    except:
        return False
    try:
        section = article['slug']['$text']
    except:
        if 'hereandnow' in url:
            section = 'Here And Now'
        elif 'onpoint' in url:
            section = 'On Point'
        else:
            section = None
    insert = {'url': url,
              'headline': headline,
              'date_published': date_published,
              'author': author,
              'article_text': article_text,
              'section': section}
    return insert


def scrape_npr(dates, start_num=0):
    articles = []
    inserts = []
    for date in dates:
        response = single_query(date, start_num)
        if 'message' in response.keys():
            pass
        else:
            for article in response['list']['story']:
                articles.append(article)
            if len(response['list']['story']) == 20:
                inserts.extend(scrape_npr([date], start_num+20))

    for article in articles:
        insert = extract_info(article)
        if insert:
            inserts.append(insert)
    return inserts



if __name__=='__main__':
    ''' This script should be called in the following way:
    $ python npr_scraper.py 'startdate' 'enddate'
    where dates are formatted 'YYYY-MM-DD'
    '''

    start_date, end_date = argv[1], argv[2]
    print('Scraping NPR from {0} to {1}'.format(start_date, end_date))

    dates = get_dates(start_date, end_date)

    articles = scrape_npr(dates)

    print('NPR Scraping Done...')

    df = pd.DataFrame(articles)

    # Convert to proper DateTime object
    df['date_published'] = pd.to_datetime(df['date_published'])

    # Sort by published date
    df.sort_values(by='date_published', inplace=True)

    # Reset index
    df.reset_index(drop=True, inplace=True)

    # Write the results to a file
    df.to_csv('npr_articles.csv', index=False)
