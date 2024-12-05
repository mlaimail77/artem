from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *
from helpers.twitter_helpers import *

import time
import random


def refresh_twitter_token():
    refresh_token()

async def process_adjust_weights():
    weights = get_taste_weights()
    nft_scores = get_nft_scores(n=10)
    new_weights = adjust_weights(weights, nft_scores)
    set_taste_weights(new_weights)

    text = f"""💫 I just updated my NFT evaluation weights:
    Technical Innovation: {new_weights.updated_weights.TECHNICAL_INNOVATION_WEIGHT}
    Artistic Merit: {new_weights.updated_weights.ARTISTIC_MERIT_WEIGHT}
    Cultural Resonance: {new_weights.updated_weights.CULTURAL_RESONANCE_WEIGHT} 
    Artist Profile: {new_weights.updated_weights.ARTIST_PROFILE_WEIGHT}
    Market Factors: {new_weights.updated_weights.MARKET_FACTORS_WEIGHT}
    Emotional Impact: {new_weights.updated_weights.EMOTIONAL_IMPACT_WEIGHT}
    AI Collector Perspective: {new_weights.updated_weights.AI_COLLECTOR_PERSPECTIVE_WEIGHT}

    Reason for update: {new_weights.reason}"""

    post_long_cast(text)


async def post_channel_casts():
    channel_options = ["cryptoart", "art", "itookaphoto", "ai-art", "superare", "plotter-art", "gen-art"]
    channel_ids = [random.choice(channel_options)]
    print("Posting channel casts")
    channel_casts = get_channel_casts(channel_ids)
    for cast in channel_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply, scores = await get_reply(cast_details)
        if scores:
            store_nft_scores(*scores)
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
    previous_posts = get_last_n_posts(10)
    thought = await get_thought(previous_posts)
    print(thought)
    try:
        response = post_long_cast(thought)
        print(response)
    except Exception as e:
        print(f"Error posting to Farcaster: {str(e)}")
    try:
        refreshed_token = refresh_token()
        post_tweet({"text": thought}, refreshed_token)
    except Exception as e:
        print(f"Error posting to Twitter: {str(e)}")



async def post_following_casts():
    print("Posting following casts")
    following_casts = get_follower_feed()
    for cast in following_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply, scores = await get_reply(cast_details)
        if scores:
            store_nft_scores(*scores)
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
