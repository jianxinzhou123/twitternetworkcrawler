import twitter
import sys
import time
from functools import partial
from sys import maxsize as maxint

def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None, friends_limit=maxint, followers_limit=maxint):
    
    assert (screen_name != None) != (user_id != None), "Must have screen_name or user_id, but not both"

    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids,count=5000)
    friends_ids, followers_ids = [], []
                              
    for twitter_api_func, limit, ids, label in [[get_friends_ids, friends_limit, friends_ids, "friends"], [get_followers_ids, followers_limit, followers_ids, "followers"]]:
        if limit == 0:
            continue

        cursor = -1
        while cursor != 0:# Use make_twitter_request via the partially bound callable...
            if screen_name:
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else: # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)
            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']

            print('Fetched {0} total {1} ids for {2}'.format(len(ids), label, (user_id or screen_name)),file=sys.stderr)
                    
            if len(ids) >= limit or response is None:
                break
                                                                      
                    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]

def oauth_login():
    
    CONSUMER_KEY = 'RLLdkysFGMypApj6MKJEUuRSZ'
    CONSUMER_SECRET = 'ZSVU6YMkVl0b9eKRZktlbf3ztV5ImyCmouLtCieVP4JIwgrUG3'
    OAUTH_TOKEN = '1038443235155353600-iRl55iDNrNlxBFTmD6hoxLUwchL6Uy'
    OAUTH_TOKEN_SECRET = 'qAmFlhK0VgnDx1X0yXC1pXVPmKxNHADnBsilRihsGdCEd'
    
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        
    twitter_api = twitter.Twitter(auth=auth)
    return twitter_api


def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw):
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e
        
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429:
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...Sleeping...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print('...Sleeping...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'.format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    wait_period = 2
    error_count = 0
    
    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise

def get_reciprocal_friends(twitter_api, screen_name=None, friends_limit=maxint, followers_limit=maxint):
    
    response = make_twitter_request(twitter_api.friends.ids,screen_name=screen_name, count = friends_limit)
    friends = response["ids"]

    response = make_twitter_request(twitter_api.followers.ids, screen_name=screen_name, count = followers_limit)
    followers = response["ids"]
    
    reciprocal_friends = set(friends) & set(followers)
    return reciprocal_friends


def get_user_profile(twitter_api, screen_names=None, user_ids=None):
    
    assert (screen_names != None) != (user_ids != None), "Must have screen_names or user_ids, but not both"
    items_to_info = {}
    items = screen_names or user_ids
    
    while len(items) > 0:
        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup, screen_name=items_str)
        else: # user_ids
            response = make_twitter_request(twitter_api.users.lookup, user_id=items_str)
    
        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else: # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info


