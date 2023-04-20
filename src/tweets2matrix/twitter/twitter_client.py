#!/usr/bin/env python

"""
TODO:
- consider poll limits (one per minute); poll every five minutes
- main loop
- json or yaml based configuration
- reload config based on HUP command
"""

import logging
import sys
from collections import defaultdict, deque
from enum import Enum
from pathlib import Path

from twitter.api import *
from twitter.oauth import OAuth, read_token_file

from tweets2matrix.store.filesystemstorage import FileSystemStorage

logging.basicConfig(level=logging.INFO)

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

    def __init__(self):
        self.twitter = Twitter(auth=self.get_oauth_token())
        self.storage = FileSystemStorage(STORAGE_DIR)
        self.since_ids = defaultdict(int)
        self.known_tweet_ids = deque(maxlen=KNOWN_TWEETS_LIST_SIZE)

        credential = self.twitter.account.verify_credentials()
        logging.info(f'Successfully authenticated user {credential["screen_name"]}')

    @staticmethod
    def get_oauth_token():
        """
        Returns:
             A Twitter OAuth token.
        """
        if not TWITTER_OAUTH.exists():
            logging.error(f'No twitter credentials in {TWITTER_OAUTH} found.')
            sys.exit()

        oauth_token, oauth_token_secret = read_token_file(str(TWITTER_OAUTH))
        app_consumer_key, app_consumer_secret = read_token_file(str(TWITTER_CONSUMER))
        return OAuth(oauth_token, oauth_token_secret, app_consumer_key, app_consumer_secret)

    def get_new_tweets(self, tweets):
        """
        Return:
            Tweets that haven't been seen yet
        """
        result = []
        for tweet in tweets:
            tweet_id = tweet['id']
            if tweet_id > self.since_ids['home_timeline']:
                self.since_ids['home_timeline'] = tweet_id
            if tweet_id not in self.known_tweet_ids and not self.storage.exists(tweet_id):
                result.append(tweet)
                self.known_tweet_ids.append(tweet_id)
                self.storage.store(tweet_id, tweet)
        return result

    def get_home_timeline(self, count: int = 25):
        kwargs = {'count': count}
        if self.since_ids['home_timeline']:
            kwargs['since_id'] = self.since_ids['home_timeline']
        return self.get_new_tweets(self.twitter.statuses.home_timeline(**kwargs))

    def search(self, query: str, result_type: TwitterSearchType = TwitterSearchType.mixed,
               result_lang: TwitterSearchLanguage = TwitterSearchLanguage.en, count: int = 100):
        kwargs = {'count': min(count, 100),
                  'result_type': result_type.name,
                  'lang': result_lang.name,
                  'q': query}
        return self.get_new_tweets(self.twitter.search.tweets(**kwargs)['statuses'])


twitter = TwitterClient()
print(twitter.search('creditsuisse', lang=TwitterSearchLanguage.de))
# print(twitter.get_home_timeline())
