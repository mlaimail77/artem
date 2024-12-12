import os
import time
import random

from utils import create_app
from celery import shared_task


# from celery import Celery
from celery.utils.log import get_task_logger
from asgiref.sync import async_to_sync

from cron_tasks import *
from webhook_tasks import *

import time


flask_app = create_app()
celery_app = flask_app.extensions["celery"]

logger = get_task_logger(__name__)

@shared_task(ignore_result=False, name="twitter_post_batch_nfts")
def sync_twitter_post_batch_nfts():
    async_to_sync(twitter_post_batch_nfts)()

@shared_task(ignore_result=False, name="reply_to_followers")
def sync_reply_to_followers():
    async_to_sync(reply_to_followers)()

@shared_task(ignore_result=False, name="post_thought_twitter_only")
def sync_post_thought_twitter_only(post_on_twitter=True, post_on_farcaster=False, post_type=None):
    POST_CLASSES = {
        "community_engagement": 0.15,
        "community_response_kol": 0.3,
        "random_thoughts": 0.2,
        "shitpost": 0.1
    }
    post_type = random.choices(
        list(POST_CLASSES.keys()),
        weights=list(POST_CLASSES.values())
    )[0]
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type)

@shared_task(ignore_result=False, name="post_artto_promotion")
def sync_post_artto_promotion(post_on_twitter=True, post_on_farcaster=True):
    async_to_sync(post_artto_promotion)(post_on_twitter, post_on_farcaster)

@shared_task(ignore_result=False, name="answer_specific_cast")
def sync_answer_specific_cast(hash):
    async_to_sync(answer_specific_cast)(hash)

@shared_task(ignore_result=False, name="reply_twitter_mentions")
def sync_reply_twitter_mentions():
    async_to_sync(reply_twitter_mentions)()

@shared_task(ignore_result=False, name="refresh_twitter_token")
def sync_refresh_twitter_token():
    refresh_twitter_token()

@shared_task(ignore_result=False, name="post_channel_casts")
def sync_post_channel_casts():
    async_to_sync(post_channel_casts)()

@shared_task(ignore_result=False, name="post_thought_farcaster_only")
def sync_post_thought_farcaster_only(post_on_twitter=False, post_on_farcaster=True, post_type=None):
    sleep_time = random.randint(0, 600)
    print(f"Post thought task started; sleeping for {sleep_time} seconds")
    time.sleep(sleep_time)
    POST_CLASSES = {
        "community_engagement": 0.2,
        "community_response_kol": 0.3,
        "random_thoughts": 0.2,
        "shitpost": 0.1
    }
    post_type = random.choices(
        list(POST_CLASSES.keys()),
        weights=list(POST_CLASSES.values())
    )[0]
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type)

@shared_task(ignore_result=False, name="post_following_casts")
def sync_post_following_casts():
    async_to_sync(post_following_casts)()

@shared_task(ignore_result=False, name="post_trending_nfts")
def sync_post_trending_nfts(post_on_twitter=True, post_on_farcaster=True):
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type="trending_collections")

@shared_task(ignore_result=False, name="post_top_nfts")
def sync_post_top_nfts(post_on_twitter=True, post_on_farcaster=True):
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type="top_collections")

@shared_task(ignore_result=False, name="post_24_hoa_tweets")
def sync_post_24_hoa_tweets(post_on_twitter=True, post_on_farcaster=True):
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type="community_response_24_hoa")

@shared_task(ignore_result=False, name="process_webhook")
def sync_process_webhook(webhook_data):
    async_to_sync(process_webhook)(webhook_data)

@shared_task(ignore_result=False, name="process_neynar_webhook")
def sync_process_neynar_webhook(webhook_data):
    async_to_sync(process_neynar_webhook)(webhook_data)

@shared_task(ignore_result=False, name="adjust_weights")
def sync_adjust_weights():
    async_to_sync(process_adjust_weights)()