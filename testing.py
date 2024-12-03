from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *


import asyncio
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
    print(trending_post)
    # response = post_long_cast(trending_post)
    # print(response)


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

async def get_final_decision_post():
    metadata = await get_nft_metadata("ethereum", "0x009c5b7fF119972e3437b51C4F94ADDB8DBB2bCd", "54")

    # metadata = await get_nft_metadata("base", "0x7d210dae7A88Cadac22cEfa9cB5baA4301B5C256", "11")
    artwork_analysis = await get_nft_analysis(metadata)
    print(artwork_analysis)
    final_decision = await get_final_decision(artwork_analysis)
    print(final_decision)

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

async def main():
    await post_thought_about_feed()

    # respond_to = "hey @artto_ai - can you share your thoughts on this NFT? https://opensea.io/assets/ethereum/0xe70659b717112ac4e14284d0db2f5d5703df8e43/347"
    # response = await get_reply(respond_to)
    # print(response)
    # Replies
    # ACK image: 0xe3ebef0e7f2ee4abb452f58e31c968b8f0496f3f
    # Text cast: 0xa0518c9d286738aeeffb95af437f1c7291f7ce0f
    # NFT LINK: 0xf9c082234c66fdad818ae9f999e21d15eff7b601
    # REPLY: 0x23f421e3c9f405beaf963cc9e5890261f90a200b

    # casts = get_casts("0xf9c082234c66fdad818ae9f999e21d15eff7b601")

    # cast = casts["cast"]

    # print(json.dumps(cast, indent=2))

    # cast_details = get_cast_details(cast)

    # print(json.dumps(cast_details, indent=2))

    # reply = await get_reply(cast_details)
    # print(reply)
    # hash = cast_details["hash"]

    # response = post_long_cast(reply, parent=hash)
    # print(response)

# asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())