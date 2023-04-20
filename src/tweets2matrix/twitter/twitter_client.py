#!/usr/bin/env python

"""
TODO:
- consider poll limits (one per minute); poll every five minutes
- main loop
- json or yaml based configuration
- reload config based on HUP command
"""

import logging
from collections import defaultdict, deque
from enum import Enum
from pathlib import Path

from twitter.api import *
from twitter.oauth import OAuth

from tweets2matrix.store.filesystemstorage import FileSystemStorage


# maximum number of results returned by the API
# (this is a Twitter API limit)
MAX_RESULT_COUNT = 100

KNOWN_TWEETS_LIST_SIZE = 5000
STORAGE_DIR = 'twitter_data'
TWITTER_OAUTH = Path('~/.rainbow_oauth').expanduser()
TWITTER_CONSUMER = Path('~/.twitter_consumer').expanduser()


class TwitterSearchType(Enum):
    mixed = 0
    recent = 1
    popular = 2


class TwitterSearchLanguage(Enum):
    en = 0
    de = 1
    fr = 2
    it = 3


class TwitterClient:

    def __init__(self, oauth_token: str, oauth_token_secret: str, app_consumer_key: str, app_consumer_secret: str):
        auth_token = OAuth(oauth_token, oauth_token_secret, app_consumer_key, app_consumer_secret)
        self.twitter = Twitter(auth=auth_token)
        self.storage = FileSystemStorage(STORAGE_DIR)
        self.since_ids = defaultdict(int)
        self.known_tweet_ids = deque(maxlen=KNOWN_TWEETS_LIST_SIZE)

        credential = self.twitter.account.verify_credentials()
        logging.info(f'Successfully authenticated user {credential["screen_name"]}')

    def get_new_tweets(self, tweets):
        """
        Return:
            Tweets that haven't been seen yet
        """
        result = []
        for tweet in reversed(tweets):    # chronological order
            tweet_id = tweet['id']
            if tweet_id > self.since_ids['home_timeline']:
                self.since_ids['home_timeline'] = tweet_id
            if tweet_id not in self.known_tweet_ids and not self.storage.exists(tweet_id):
                result.append(tweet)
                self.known_tweet_ids.append(tweet_id)
                self.storage.store(tweet_id, tweet)
        return result

    def get_home_timeline(self, count: int = 25):
        kwargs = {'count': min(count, MAX_RESULT_COUNT),
                  'tweet_mode': 'extended'}
        if self.since_ids['home_timeline']:
            kwargs['since_id'] = self.since_ids['home_timeline']
        return self.get_new_tweets(self.twitter.statuses.home_timeline(**kwargs))

    def search(self, q: str, result_type: TwitterSearchType = TwitterSearchType.mixed,
               result_lang: TwitterSearchLanguage = TwitterSearchLanguage.en, count: int = 100):
        """
        Search for the given queries on Twitter.

        Args:
            q: the query string
            result_type: the TwitterSearchType to search for
            result_lang: the TwitterSearchLanguage to use.
            count: maximum number of results (max. 100)
        """
        kwargs = {'count': min(count, MAX_RESULT_COUNT),
                  'result_type': result_type.name,
                  'lang': result_lang.name,
                  'tweet_mode': 'extended',
                  'q': q}

        if self.since_ids['search']:
            kwargs['since_id'] = self.since_ids['search']
        return self.get_new_tweets(self.twitter.search.tweets(**kwargs)['statuses'])

    @staticmethod
    def get_tweet_text(tweet):
        """Create a text representation of the given tweet"""
        if 'retweeted_status' in tweet:
            rt_status = tweet['retweeted_status']
            if 'extended_tweet' in rt_status:
                elem = rt_status['extended_tweet']
            else:
                elem = rt_status
            rt_text = elem['full_text'] if 'full_text' in elem else elem['text']
            tweet['full_text'] = 'RT @' + rt_status['user']['screen_name'] + ': ' + rt_text
        elif 'extended_tweet' in tweet:
            tweet['full_text'] = tweet['extended_tweet']['full_text']

        return tweet['full_text'] if 'full_text' in tweet else tweet['text']
