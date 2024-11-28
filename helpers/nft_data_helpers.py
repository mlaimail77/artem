import aiohttp
import json
import os
from dotenv import load_dotenv
import asyncio

load_dotenv('.env.local')

SIMPLEHASH_API_KEY = os.getenv('SIMPLEHASH_API_KEY')

def filter_nft_metadata(response):
    if not response:
        return None

    filtered_response = {
        'nft_id': response['nft_id'],
        'chain': response['chain'],
        'contract_address': response['contract_address'],
        'name': response['name'],
        'description': response['description'],
        'image_medium_url': response['previews']['image_medium_url'],
        'contract': response['contract'],
        'collection_name': response['collection']['name'],
        'collection_slug': response['collection']['collection_id'],
        'collection_description': response['collection']['description'],
        'distinct_owner_count': response['collection']['distinct_owner_count'],
        'distinct_nft_count': response['collection']['distinct_nft_count'], 
        'total_quantity': response['collection']['total_quantity'],
        'last_sale': response['last_sale'],
        'first_created': response['first_created'],
        'rarity': response['rarity'],
        'attributes': response['extra_metadata']['attributes']
    }
    
    return filtered_response

async def get_nft_metadata(network, contract_address, token_id, api_key=SIMPLEHASH_API_KEY):
    """
    Fetches NFT metadata from the SimpleHash API.

    Args:
        network (str): The blockchain network (e.g., 'eth', 'base').
        contract_address (str): The contract address of the NFT.
        token_id (int): The token ID of the NFT.
        api_key (str): The SimpleHash API key to use.

    Returns:
        dict: The response from the SimpleHash API containing the NFT metadata.
    """
    # Construct the API endpoint URL
    url = f"https://api.simplehash.com/api/v0/nfts/{network}/{contract_address}/{token_id}"

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    # Send the GET request
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            # Check if the response is valid
            if response.status == 200:
                response_data = await response.json()
                return filter_nft_metadata(response_data)
            else:
                # Handle the case where the API response is invalid
                print(f"Error fetching NFT metadata: {response.status}")
                return None


async def main():
    # Load environment variables from .env.local
    network = 'base'
    contract_address = '0x7d210dae7A88Cadac22cEfa9cB5baA4301B5C256'
    token_id = 11

    metadata = await get_nft_metadata(network, contract_address, token_id)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    asyncio.run(main())