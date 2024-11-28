from helpers.farcaster_helpers import *
from helpers.llm_helpers import *

if __name__ == "__main__":
    import asyncio

    # ACK image: 0xe3ebef0e7f2ee4abb452f58e31c968b8f0496f3f
    # Text cast: 0xa0518c9d286738aeeffb95af437f1c7291f7ce0f
    casts = get_casts("0xa0518c9d286738aeeffb95af437f1c7291f7ce0f")


    cast = casts["cast"]

    print(json.dumps(cast, indent=2))

    cast_details = get_cast_details(cast)

    print(json.dumps(cast_details, indent=2))

    reply = asyncio.run(generate_reply_smart(cast_details))
    print(reply)
    # print(cast_details)
    # response = post_cast("I have my own taste that will continue to evolve.")
    # print(response)