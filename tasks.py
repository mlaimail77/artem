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

@shared_task(ignore_result=False, name="post_thought_twitter_only")
def sync_post_thought_twitter_only(post_on_twitter=True, post_on_farcaster=True, post_type=None):
    post_type = random.choice([
        "Random Thoughts",
        "Shitpost"
    ])
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type)

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

@shared_task(ignore_result=False, name="post_thought_about_feed")
def sync_post_thought_about_feed(post_on_twitter=False, post_on_farcaster=True):
    async_to_sync(post_thought_about_feed)(post_on_twitter, post_on_farcaster, post_type="Community Response")

@shared_task(ignore_result=False, name="post_thought")
def sync_post_thought(post_on_twitter=False, post_on_farcaster=True, post_type=None):
    time.sleep(random.randint(0, 600))
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type)

@shared_task(ignore_result=False, name="post_following_casts")
def sync_post_following_casts():
    async_to_sync(post_following_casts)()

@shared_task(ignore_result=False, name="post_trending_nfts")
def sync_post_trending_nfts(post_on_twitter=False, post_on_farcaster=True):
    async_to_sync(post_thought)(post_on_twitter, post_on_farcaster, post_type="Trending Collections")

@shared_task(ignore_result=False, name="process_webhook")
def sync_process_webhook(webhook_data):
    async_to_sync(process_webhook)(webhook_data)

@shared_task(ignore_result=False, name="process_neynar_webhook")
def sync_process_neynar_webhook(webhook_data):
    async_to_sync(process_neynar_webhook)(webhook_data)

@shared_task(ignore_result=False, name="adjust_weights")
def sync_adjust_weights():
    async_to_sync(process_adjust_weights)()