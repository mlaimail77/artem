from celery import Celery, Task
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
            beat_schedule={
                "post_thought_every_2_hours": {
                    "task": "post_thought",
                    "schedule": 7200
                },
                "post_channel_casts_every_2_hours": {
                    "task": "post_channel_casts",
                    "schedule": 7200
                },
                "post_thought_about_feed_every_1_5_hours": {
                    "task": "post_thought_about_feed",
                    "schedule": 5400
                },
                "adjust_weights_every_24_hours": {
                    "task": "adjust_weights",
                    "schedule": 86400
                },
                "refresh_twitter_token_every_2_hours": {
                    "task": "refresh_twitter_token",
                    "schedule": 7200
                },
            },
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app
