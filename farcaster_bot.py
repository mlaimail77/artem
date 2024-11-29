from helpers.farcaster_helpers import *
from helpers.llm_helpers import *
import aiocron
import asyncio

@aiocron.crontab('*/200 * * * *')
async def reply_image_casts():
    image_casts = get_image_casts(10)
    for cast in image_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)

@aiocron.crontab('*/180 * * * *')
async def reply_trending():
    trending_casts = get_trending_casts()
    for cast in trending_casts["casts"]:
        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)

@aiocron.crontab('*/30 * * * *')
async def post_thought():
    print("Posting thought")
    previous_posts = get_last_n_posts(supabase, 10)
    thought = await get_thought(previous_posts)
    print(thought)
    response = post_long_cast(thought)
    print(response)

@aiocron.crontab('0/120 * * * *')
async def reply_mentions():
    print("Replying to mentions")
    response = search_casts("artto_ai")
    for cast in response["result"]["casts"]:
        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)


async def main():
    await reply_mentions()

if __name__ == "__main__":
    # asyncio.run(reply_trending())
    # asyncio.run(main())
    # asyncio.get_event_loop().run_forever()


    # asyncio.run(main())
    ## RANDOM THOUGHT

    # previous_posts = get_last_n_posts(supabase, 10)
    # thought = asyncio.run(get_thought())
    # print(thought)

    # response = post_long_cast(thought)
    # print(response)



    
    # # SEARCH
    # response = search_casts("artto_ai")
    # print(response)
    # response = asyncio.run(get_thought())
    # print(response)

    # # Replies
    # # ACK image: 0xe3ebef0e7f2ee4abb452f58e31c968b8f0496f3f
    # # Text cast: 0xa0518c9d286738aeeffb95af437f1c7291f7ce0f
    # # NFT LINK: 0xf9c082234c66fdad818ae9f999e21d15eff7b601
    ## REPLY: 0x23f421e3c9f405beaf963cc9e5890261f90a200b

    asyncio.run(adjust_weights())

    # casts = get_casts("0x8da3efeee5729402cc96ab5abb951828bc210356")


    # cast = casts["cast"]

    # print(json.dumps(cast, indent=2))

    # cast_details = get_cast_details(cast)

    # print(json.dumps(cast_details, indent=2))

    # reply = asyncio.run(get_reply(cast_details))
    # print(reply)
    # hash = cast_details["hash"]

    # response = post_long_cast(reply, parent=hash)
    # print(response)



    # # NEW CAST

    # print(cast_details)
    # response = post_cast("I have my own taste that will continue to evolve.")
    # print(response)