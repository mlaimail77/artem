from flask import Flask, request, jsonify
from flask_apscheduler import APScheduler
import os

from helpers.utils import get_supabase_client
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *

from dotenv import load_dotenv

load_dotenv('.env.local')

app = Flask(__name__)
app.secret_key = os.urandom(50)

scheduler = APScheduler()

supabase = get_supabase_client()

@app.route('/neynar-webhook', methods=['POST'])
async def neynar_webhook():
    try:
        data = request.json        
        # Extract relevant data from webhook payload
        cast = data.get('data', {})

        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler.task('cron', id='tweet_task', hour='12', minute='0')
async def adjust_weights():
    text = await adjust_weights()
    print(text)
    response = post_long_cast(text)
    print(response)

@scheduler.task('cron', id='tweet_task', minute='*/30')
async def post_thought():
    print("Posting thought")
    previous_posts = get_last_n_posts(supabase, 10)
    thought = await get_thought(previous_posts)
    print(thought)
    response = post_long_cast(thought)
    print(response)


@scheduler.task('cron', id='post_following_casts', hour='*/2')
async def post_following_casts():
    print("Posting following casts")
    following_casts = get_follower_feed()
    for cast in following_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)


@scheduler.task('cron', id='tweet_task', hour='*')
async def post_channel_casts():
    channel_options = ["cryptoart", "art", "itookaphoto", "ai-art", "superare", "plotter-art", "gen-art"]
    channel_ids = [random.choice(channel_options)]
    print("Posting channel casts")
    channel_casts = get_channel_casts(channel_ids)
    for cast in channel_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)

if __name__ == '__main__':
    app.run(debug=True, 
            port=int(os.getenv('PORT', 3000)))
    scheduler.init_app(app)
    scheduler.start()