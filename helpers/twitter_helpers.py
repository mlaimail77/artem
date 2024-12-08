import base64
import hashlib
import os
import re
import json
import requests
import redis
from twikit import Client
import aiohttp
from datetime import datetime, timedelta
from requests.auth import AuthBase, HTTPBasicAuth
from requests_oauthlib import OAuth2Session, TokenUpdated

from helpers.utils import *

from dotenv import load_dotenv

load_dotenv('.env.local')

# Twikit client
twikit_client = Client('en-US')

r = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost'))


client_id = os.environ.get("X_CLIENT_ID")
client_secret = os.environ.get("X_CLIENT_SECRET")
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.environ.get("X_REDIRECT_URI", "http://127.0.0.1:8000/oauth/callback")

scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]

code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")

async def get_twikit_client():
    if os.path.exists('cookies.json'):
        twikit_client.load_cookies('cookies.json')
    else:
        await twikit_client.login(
            auth_info_1=os.environ.get("TWITTER_USERNAME"),
            auth_info_2=os.environ.get("TWITTER_EMAIL"),
            password=os.environ.get("TWITTER_PASSWORD")
        )
        twikit_client.save_cookies('cookies.json')

async def post_tweet(payload, token, parent=None):    
    print("Attempting to tweet!")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            headers={
                "Authorization": "Bearer {}".format(token["access_token"]),
                "Content-Type": "application/json",
            }
        ) as response:
            response_json = await response.json()
            print(f"Tweet Response: {response_json}")
            if response.status == 429:
                reset_time = response.headers.get('x-rate-limit-reset')
                limit = response.headers.get('x-rate-limit-limit')
                remaining = response.headers.get('x-rate-limit-remaining')
                print(f"Rate limit ceiling: {limit}")
                print(f"Remaining requests: {remaining}")
                reset_timestamp = datetime.fromtimestamp(int(reset_time))
                minutes_until_reset = (reset_timestamp - datetime.now()).total_seconds() / 60
                print(f"Rate limit reset time: {reset_timestamp} ({minutes_until_reset:.1f} minutes from now)")


            if response.status == 200:
                print(f"Tweet posted successfully: {response_json}")
                post = {
                    'hash': response_json['data']['id'],
                    'text': payload['text'],
                    'parent_id': parent
                }
                return post
            elif response.status != 200:
                print(f"Error posting tweet: {response_json}")
                print(f"Trying twikit client...")
                try:
                    await get_twikit_client()
                    response =await twikit_client.create_tweet(
                        text=payload['text'],
                        reply_to=parent
                    )
                    post = {
                        'hash': response.id,
                        'text': payload['text'],
                        'parent_id': parent
                    }
                    return post
                except Exception as e:
                    print(f"Error posting tweet: {e}")
                
            return None


def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)


def refresh_token():
    twitter = make_token()

    t = r.get("token")
    bb_t = t.decode("utf8").replace("'", '"')
    data = json.loads(bb_t)

    refreshed_token = twitter.refresh_token(
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        refresh_token=data["refresh_token"],
    )

    st_refreshed_token = '"{}"'.format(refreshed_token)
    j_refreshed_token = json.loads(st_refreshed_token)
    r.set("token", j_refreshed_token)
    return refreshed_token

def search_twitter(query, bearer_token, max_results=10):
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {
        'query': query,
        'tweet.fields': 'author_id',
        'expansions': 'attachments.media_keys', 
        'media.fields': 'preview_image_url,url,type',
        'max_results': max_results
    }

    def bearer_oauth(r):
        r.headers["Authorization"] = f"Bearer {bearer_token}"
        r.headers["User-Agent"] = "v2RecentSearchPython"
        return r

    response = requests.get(search_url, auth=bearer_oauth, params=query_params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def get_twitter_mentions(bearer_token, max_results=50):
    query = "@artto__agent"
    return search_twitter(query, bearer_token, max_results)

def get_24_HOA_tweets(bearer_token, max_results=25):
    # Get tweets from the last 7 days
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    query = f'"24 Hours of Art" -filter:replies from:RogerDickerman since:{seven_days_ago}'
    return search_twitter(query, bearer_token, max_results)

def search_twitter_images(query, bearer_token, max_results=50):
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {
        'query': query,
        'tweet.fields': 'author_id,entities',
        'expansions': 'attachments.media_keys',
        'media.fields': 'preview_image_url,url,type',
        'max_results': max_results
    }

    def bearer_oauth(r):
        r.headers["Authorization"] = f"Bearer {bearer_token}"
        r.headers["User-Agent"] = "v2RecentSearchPython"
        return r

    response = requests.get(search_url, auth=bearer_oauth, params=query_params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    json_response = response.json()

    print(json_response)

    # Extract media URLs from the response
    media_dict = {}
    if 'includes' in json_response and 'media' in json_response['includes']:
        media_dict = {media['media_key']: media.get('url', '') for media in json_response['includes']['media']}

    tweets = []
    if 'data' in json_response:
        for tweet in json_response['data']:
            media_url = ''
            if 'attachments' in tweet and 'media_keys' in tweet['attachments']:
                media_url = media_dict.get(tweet['attachments']['media_keys'][0], '')

            tweet_text = tweet['text']
            if 'entities' in tweet and 'urls' in tweet['entities'] and len(tweet['entities']['urls']) > 0:
                tweet_text += " URL: " + tweet['entities']['urls'][0]['expanded_url']

            tweet_obj = {
                'id': tweet['id'],
                'text': tweet_text,
                'url': media_url,
                'author_id': tweet.get('author_id', None)
            }
            tweets.append(tweet_obj)

    return tweets


def main():
    refreshed_token = refresh_token()
    post_tweet({"text": "🎨🖌️🎨🖌️🎨🖌️"}, refreshed_token)

if __name__ == "__main__":
    main()
