import aiohttp
import json
import os
import asyncio

from dotenv import load_dotenv

load_dotenv('.env.local')

SIMPLEHASH_API_KEY = os.getenv('SIMPLEHASH_API_KEY')

async def get_wallet_nfts(wallet_address: str, networks: list = ['ethereum', 'base'], limit: int = 20, api_key: str = SIMPLEHASH_API_KEY):
    """
    Fetches NFTs owned by a specific wallet address from the SimpleHash API.

    Args:
        wallet_address (str): The wallet address to fetch NFTs for
        networks (list): List of blockchain networks to include. Default: ['ethereum', 'base']
        limit (int): Maximum number of NFTs to return. Default: 20
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY

    Returns:
        dict: The response from the SimpleHash API containing the wallet's NFTs
    """
    # Join networks with comma for URL parameter
    networks_param = ','.join(networks)
    
    # Construct the API endpoint URL
    url = f"https://api.simplehash.com/api/v0/nfts/owners_v2?chains={networks_param}&wallet_addresses={wallet_address}&limit={limit}&order_by=transfer_time__desc"

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

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

async def get_trending_collections(time_period='24h', chains=['ethereum', 'base', 'solana'], limit=20, api_key=SIMPLEHASH_API_KEY):
    """
    Fetches trending NFT collections from the SimpleHash API.

    Args:
        time_period (str): Time period for trending data. Options: '24h', '1d', '7d', '30d'. Default: '24h'
        chains (list): List of blockchain networks to include. Default: ['ethereum', 'base', 'solana']
        limit (int): Number of collections to return. Default: 100
        api_key (str): The SimpleHash API key to use.

    Returns:
        dict: The response from the SimpleHash API containing trending collections data.
    """
    # Construct chains parameter
    chains_param = '%2C'.join(chains)
    
    # Construct the API endpoint URL
    url = f"https://api.simplehash.com/api/v0/nfts/collections/trending?chains={chains_param}&time_period={time_period}&limit={limit}"

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    # Send the GET request
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            # Check if the response is valid
            if response.status == 200:
                return await response.json()
            else:
                # Handle the case where the API response is invalid
                print(f"Error fetching trending collections: {response.status}")
                return None

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
                print(response_data)
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