from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *

import time
import random

async def post_channel_casts():
    channel_options = ["cryptoart", "art", "itookaphoto", "ai-art", "superare", "plotter-art", "gen-art"]
    current_hour = datetime.now().hour
    channel_ids = [channel_options[current_hour % len(channel_options)]]
    print("Posting channel casts")
    channel_casts = get_channel_casts(channel_ids)
    for cast in channel_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)
        print("Waiting 10-30 seconds")
        time.sleep(random.randint(10, 30))


async def post_trending_nfts():
    print("Posting trending NFTs cast")
    trending_collections = await get_trending_collections()
    trending_post = await get_trending_post(trending_collections)
    response = post_long_cast(trending_post)
    print(response)


async def post_thought():
    print("Posting thought")
    previous_posts = get_last_n_posts(supabase, 10)
    thought = await get_thought(previous_posts)
    print(thought)
    response = post_long_cast(thought)
    print(response)

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
        print("Waiting 10-30 seconds")
        time.sleep(random.randint(10, 30))

async def post_thought_about_feed():
    trending_casts = get_trending_casts()
    print("Getting trending casts")
    filtered_casts = []
    for cast in trending_casts["casts"]:
        filtered_cast = {
            "author": cast["author"]['username'],
            "text": cast["text"]
        }
        filtered_casts.append(filtered_cast)
    thought = await get_thoughts_on_trending_casts(filtered_casts)
    print(thought)
    response = post_long_cast(thought)
    print(response)
    
async def post_cast_about_feed():
    print("Posting cast about feed")

