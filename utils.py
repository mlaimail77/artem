from celery import Celery, Task
from celery.schedules import crontab
from flask import Flask
import os

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost'),
            result_backend=os.getenv('CELERY_BROKER_URL', 'redis://localhost'),
            task_ignore_result=True,
            timezone='America/New_York',
            beat_schedule={
                "post_recent_activity_every_day_at_2PM": {
                    "task": "post_recent_activity",
                    "schedule": crontab(minute=0, hour='14')
                },

                "sell_and_post_nfts_daily": {
                    "task": "sell_and_post_nfts",
                    "schedule": crontab(minute=30, hour=14)
                },

                # Farcaster only
                # at 20 minutes past the hour
                "post_thought_farcaster_only_every_hour": {
                    "task": "post_thought_farcaster_only", 
                    "schedule": crontab(minute='20', hour='*/1')
                },

                # Promotional Posts at 9:05 and 21:05
                "post_artto_promotion_every_12_hours": {
                    "task": "post_artto_promotion",
                    "schedule": crontab(minute=5, hour='9,21')
                },

                "post_rewards_summary_every_12_hours": {
                    "task": "post_rewards_summary",
                    "schedule": crontab(minute=0, hour='11,23')
                },

                "post_simple_analysis_nfts_every_4_hours": {
                    "task": "post_simple_analysis_nfts",
                    "schedule": crontab(minute=45, hour='*/4')
                },

                "add_nfts_to_discovery_every_4_hours": {
                    "task": "add_nfts_to_discovery",
                    "schedule": crontab(minute=0, hour='*/4')
                },

                "analyze_nfts_in_discovery_every_4_hours": {
                    "task": "analyze_nfts_in_discovery",
                    "schedule": crontab(minute=10, hour='*/4')
                },

                # Farcaster Only
                "post_channel_casts_every_2_hours": {
                    "task": "post_channel_casts",
                    "schedule": crontab(minute=0, hour='*/2')
                },

                # Farcaster and Twitter
                "post_24_hoa_tweets_every_day_at_4PM": {
                    "task": "post_24_hoa_tweets",
                    "schedule": crontab(minute=25, hour='16')
                },

                # Farcaster and Twitter
                "post_trending_nfts_every_day_at_6PM": {
                    "task": "post_trending_nfts",
                    "schedule": crontab(minute=57, hour='18')
                },

                # Farcaster and Twitter
                "post_top_nfts_every_day_at_8PM": {
                    "task": "post_top_nfts",
                    "schedule": crontab(minute=12, hour='20')
                },

                "post_batch_nfts_every_1_hour": {
                    "task": "post_batch_nfts",
                    "schedule": crontab(minute=10, hour='*/1')
                },

                "post_thought_twitter_only_every_3_hours": {
                    "task": "post_thought_twitter_only",
                    "schedule": crontab(minute=15, hour='9,12,15,18,21,0')
                },

                # Twitter Only
                "reply_to_followers_every_4_hours": {
                    "task": "reply_to_followers",
                    "schedule": crontab(minute=30, hour='*/4')
                },

                # Twitter Only
                "reply_twitter_mentions_every_6_hours": {
                    "task": "reply_twitter_mentions",
                    "schedule": crontab(minute=45, hour='*/6')
                },

                "adjust_weights_every_24_hours": {
                    "task": "adjust_weights",
                    "schedule": crontab(minute=0, hour='10,22')
                },
    
                "refresh_twitter_token_every_2_hours": {
                    "task": "refresh_twitter_token",
                    "schedule": 7200
                },

                "post_trending_nfts_every_at_10AM": {
                    "task": "post_trending_nfts",
                    "schedule": crontab(minute=30, hour='10')
                },

                "check_balance_and_top_up": {
                    "task": "check_balance_and_top_up",
                    "schedule": crontab(minute=0, hour='6')
                },

                "generate_memory": {
                    "task": "generate_memory",
                    "schedule": crontab(minute=0, hour='0,12')
                },
            },
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app
