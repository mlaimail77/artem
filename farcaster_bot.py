from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *

import aiocron
import asyncio
import time
import random

@aiocron.crontab('*/100 * * * *')
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


@aiocron.crontab('15,45 * * * *')
async def post_thought():
    print("Posting thought")
    previous_posts = get_last_n_posts(supabase, 10)
    thought = await get_thought(previous_posts)
    print(thought)
    response = post_long_cast(thought)
    print(response)

@aiocron.crontab('0/120 * * * *')
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

if __name__ == "__main__":
    asyncio.get_event_loop().run_forever()