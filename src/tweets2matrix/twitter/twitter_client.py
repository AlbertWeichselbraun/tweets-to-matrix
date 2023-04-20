import sys
from pathlib import Path

from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from twiter.api import *
from twitter.oauth import OAuth, read_token_file
from twitter.oauth_dance import import oauth_dance
from twitter.util import printNicely

TWITTER_OAUTH = Path('~/.rainbow_oauth').expanduser()
TWITTER_OAUTH = Path('~/.twitter_consumer').expanduser()




class TwitterClient:

    def __init__(self):
        if not TWITTER_OAUTH.exists():
            print(f'No twitter credentials in {TWITTER_OAUTH} found.')
            sys.exit()

        oauth_token, oauth_token_secret = read_token_file(str(TWITTER_OAUTH))
