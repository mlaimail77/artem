from openai import OpenAI
import os
import asyncio
import json

from helpers.nft_data_helpers import *
from helpers.prompts.llm_prompts import *

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_nft_opinion",
            "description": "Get the opinion of an NFT provided by as a link the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "The network the NFT is on: base, ethereum, etc."
                    },
                    "contract_address": {
                        "type": "string",
                        "description": "The contract address of the NFT, typically a long string of numbers and letters"
                    },
                    "token_id": {
                        "type": "string",
                        "description": "The token ID of the NFT, typically a number"
                },
                "required": ["network", "contract_address", "token_id"],
                "additionalProperties": False,
                },
            },
        }
    }
]


async def get_nft_opinion(network, contract_address, token_id):
    metadata = await get_nft_metadata(network, contract_address, token_id)
    pretty_metadata = json.dumps(metadata, indent=2)

    system_prompt = SYSTEM_PROMPT_GET_NFT_OPINION.format(metadata=pretty_metadata)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
             "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": metadata["image_medium_url"]
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content

async def get_image_opinion(cast_details):

    author_details = f"{cast_details['display_name']} ({cast_details['username']}) - BIOGRAPHY:{cast_details['bio']}"
    cast_text = f"{author_details}\n\nText:{cast_details['text']}"


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
             "content": SYSTEM_PROMPT_IMAGE_REPLY},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": cast_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": cast_details["image_url"]
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )

    return response.choices[0].message.content


async def get_reply(cast_details):

    author_details = f"{cast_details['display_name']} ({cast_details['username']}) - BIOGRAPHY:{cast_details['bio']}"
    cast_text = f"{author_details}\n\nText:{cast_details['text']}"

    if cast_details["image_url"]:
        print("Generating image opinion")
        return await get_image_opinion(cast_details)

    print("Generating reply to text-only cast")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
            "content": SYSTEM_PROMPT_REPLY + cast_text},
        ],
        tools=tools,
        max_tokens=300
    )

    if response.choices[0].message.tool_calls:
        print("Tool call")
        tool_call = response.choices[0].message.tool_calls[0]
        tool_input = json.loads(tool_call.function.arguments)
        print(tool_input)
        print("Getting NFT opinion")
        return await get_nft_opinion(**tool_input)

    return response.choices[0].message.content

def get_thought(previous_thoughts="No recent thoughts"):
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", 
        "content": SYSTEM_PROMPT_TWEET + previous_thoughts},
    ],
    max_tokens=300
    )

    print(SYSTEM_PROMPT_TWEET + previous_thoughts)

    return response.choices[0].message.content

def split_tweet(tweet):
    # If tweet is already under limit, return as single item array
    if len(tweet) <= 280*2:
        return [tweet]
    
    words = tweet.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        # Add 1 for the space between words
        word_length = len(word) + (1 if current_chunk else 0)
        
        if current_length + word_length <= 280*2:
            current_chunk.append(word)
            current_length += word_length
        else:
            # Store current chunk and start new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
    
    # Add final chunk if exists
    if current_chunk:
        chunks.append(' '.join(current_chunk))
        
    return chunks


async def main():

    response = await generate_reply_smart("hey @artto_ai - can you share your thoughts on this NFT? https://opensea.io/assets/ethereum/0xe70659b717112ac4e14284d0db2f5d5703df8e43/347")
    print(response)

    # response = await generate_reply_smart("yo @artto_ai would you buy this? https://basescan.org/nft/0x7d210dae7a88cadac22cefa9cb5baa4301b5c256/57")
    # print(response)

    # response = await generate_reply_smart("yo @artto_ai what kind of art do you like?")

    # print(response)



    # metadata = await get_nft_opinion("base", "0x7d210dae7A88Cadac22cEfa9cB5baA4301B5C256", "11")
    # print(metadata)
    # response = generate_image_reply({
    #     "text": "4. The Giving Tree @JohnKnopfPhotos",
    #     "url": "https://pbs.twimg.com/media/GdQCrG0XoAAttBL.jpg"
    # })
    # print(response)

if __name__ == "__main__":
    asyncio.run(main())