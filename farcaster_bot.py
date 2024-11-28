from helpers.farcaster_helpers import *
from helpers.llm_helpers import *

if __name__ == "__main__":
    import asyncio
    ## SEARCH
    # response = search_casts("artto_ai")
    # print(response)
    # response = asyncio.run(get_thought())
    # print(response)

    # ACK image: 0xe3ebef0e7f2ee4abb452f58e31c968b8f0496f3f
    # Text cast: 0xa0518c9d286738aeeffb95af437f1c7291f7ce0f
    # NFT LINK: 0xf9c082234c66fdad818ae9f999e21d15eff7b601

    casts = get_casts("0xf9c082234c66fdad818ae9f999e21d15eff7b601")


    cast = casts["cast"]

    print(json.dumps(cast, indent=2))

    cast_details = get_cast_details(cast)

    print(json.dumps(cast_details, indent=2))

    reply = asyncio.run(get_reply(cast_details))
    print(reply)

    hash = cast_details["hash"]
    print(hash)

    response = post_long_cast(reply, parent=hash)
    print(response)




    # print(cast_details)
    # response = post_cast("I have my own taste that will continue to evolve.")
    # print(response)