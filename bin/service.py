#!/usr/bin/env python

import time
import logging
from json import load
from sys import argv

from tweets2matrix.matrix import MatrixClient
from tweets2matrix.twitter.twitter_client import TwitterClient, TwitterSearchLanguage, TwitterSearchType

logging.basicConfig(level=logging.INFO)


def format_tweet(tweet):
    return f'From: {tweet["user"]["name"]} ({tweet["user"]["id"]})\n' \
           f'Date: {tweet["created_at"]}\n' \
           f'Hashtags: {", ".join([t ["text"] for t in tweet["entities"].get("hashtags", [])])}\n' \
           f'Media: {", ".join([t["media_url"] for t in tweet["entities"].get("media", [])])}\n' \
           f'URLs: {", ".join([t["expanded_url"] if "expanded_url" in t else t["url"] for t in tweet["entities"].get("urls", [])])}\n' \
           f'\n' \
           f'{twitter.get_tweet_text(tweet)}\n'


# read and verify configuration
with open(argv[1]) as f:
    config = load(f)
    for search_query in config['twitter_search_queries']:
        try:
            search_query['result_lang'] = TwitterSearchLanguage[search_query['result_lang']]
        except KeyError:
            raise TypeError(f'Invalid TwitterSearchLanguage: {search_query["result_lang"]}.')

        try:
            search_query['result_type'] = TwitterSearchType[search_query['result_type']]
        except KeyError:
            raise TypeError(f'Invalid TwitterSearchType: {search_query["result_type"]}.')

# setup clients
twitter = TwitterClient(**config['twitter_auth'])
matrix = MatrixClient(**config['matrix_auth'])

# event queue
while True:
    # post timeline
    logging.info('Retrieving home timeline.')
    for tweet in twitter.get_home_timeline(count=100):
        msg = format_tweet(tweet)
        logging.info(msg)
        matrix.send_matrix_message(msg)

    # post searches
    logging.info(f'Performing {len(config["twitter_search_queries"])} configured search queries.')
    for search_query in config['twitter_search_queries']:
        for tweet in twitter.search(**search_query):
            msg = format_tweet(tweet)
            logging.info(msg)
            matrix.send_matrix_message(msg)

    time.sleep(config["poll_delay_secs"])
