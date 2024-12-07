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

    print("response:", response)
    
    if not response:
        print("No response from SimpleHash API")
        return None

    # Check if response is a dictionary before accessing keys
    if not isinstance(response, dict):
        print("Invalid response format from SimpleHash API")
        return None
    
    filtered_response = {
        'nft_id': response.get('nft_id'),
        'chain': response.get('chain'),
        'contract_address': response.get('contract_address'),
        'name': response.get('name'),
        'description': response.get('description'),
        'image_medium_url': response.get('previews', {}).get('image_medium_url'),
        'contract': response.get('contract'),
        'collection_name': response.get('collection', {}).get('name'),
        'collection_id': response.get('collection', {}).get('collection_id'),
        'floor_prices': [{
            'marketplace': price.get('marketplace_name'),
            'value_eth': price.get('value', 0) / 1e18,
            'value_usd': price.get('value_usd_cents', 0) / 100
        } for price in response.get('collection', {}).get('floor_prices', [])] if response.get('collection', {}).get('floor_prices') else [],
        'collection_description': response.get('collection', {}).get('description'),
        'distinct_owner_count': response.get('collection', {}).get('distinct_owner_count'),
        'distinct_nft_count': response.get('collection', {}).get('distinct_nft_count'),
        'total_quantity': response.get('collection', {}).get('total_quantity'),
        'last_sale_usd': response.get('last_sale', {}).get('unit_price_usd_cents', 0) / 100,
        'first_created': response.get('first_created'),
        'rarity': response.get('rarity'),
        'attributes': response.get('extra_metadata', {}).get('attributes')
    }
    
    return filtered_response

def format_collections(response, time_period):
    collections = response["collections"]
    formatted_response = []
    for collection in collections:
        formatted_response.append({
            "name": collection.get("collection_details", {}).get("name"),
            "description": collection.get("collection_details", {}).get("description"),
            "chains": collection.get("collection_details", {}).get("chains", []),
            "category": collection.get("collection_details", {}).get("category"),
            "floor_prices": [{
                "marketplace": price["marketplace_name"],
                "value_eth": price["value"] / 1e18,
                "value_usd": price["value_usd_cents"] / 100
            } for price in collection.get("collection_details", {}).get("floor_prices", [])] if collection.get("collection_details", {}).get("floor_prices") else [],
            "distinct_owner_count": collection.get("collection_details", {}).get("distinct_owner_count"),
            "distinct_nft_count": collection.get("collection_details", {}).get("distinct_nft_count"), 
            "total_quantity": collection.get("collection_details", {}).get("total_quantity"),
            "volume_percent_change": collection.get("volume_percent_change"),
            "transaction_count": collection.get("transaction_count"),
            "transaction_count_percent_change": collection.get("transaction_count_percent_change"),
            "volume_usd": collection.get("volume_usd_cents", 0)/100,
            "time_period": time_period
        })
    return formatted_response


async def is_top_collection(collection_id, time_period='30d'):
    top_collections = await get_top_collections(time_period=time_period, chains=['ethereum', 'base'], limit=100)
    return collection_id in [collection['collection_id'] for collection in top_collections['collections']]

async def get_top_collections(time_period='24h', chains=['ethereum', 'base', 'solana'], limit=20, api_key=SIMPLEHASH_API_KEY):
    """
    Fetches top NFT collections from the SimpleHash API.

    Args:
        time_period (str): Time period for top collections data. Options: '24h', '1d', '7d', '30d'. Default: '24h'
        chains (list): List of blockchain networks to include. Default: ['ethereum', 'base', 'solana']
        limit (int): Number of collections to return. Default: 20
        api_key (str): The SimpleHash API key to use.

    Returns:
        dict: The response from the SimpleHash API containing top collections data.
    """
    # Construct chains parameter
    chains_param = '%2C'.join(chains)
    
    # Construct the API endpoint URL
    url = f"https://api.simplehash.com/api/v0/nfts/collections/top_v2?chains={chains_param}&time_period={time_period}&limit={limit}"

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
                print(f"Error fetching top collections: {response.status}")
                return None

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
                return response_data
            else:
                # Handle the case where the API response is invalid
                print(f"Error fetching NFT metadata: {response.status}")
                return None


async def main():
    # Load environment variables from .env.local
    network = 'ethereum'
    contract_address = '0x059EDD72Cd353dF5106D2B9cC5ab83a52287aC3a'
    token_id = 11

    top_collection = await is_top_collection('6dbbb898be7ee3c05af90199fefce18b', time_period='30d')
    print(top_collection)

    # top_collections = await get_top_collections('30d', chains=['ethereum'], limit=100)
    # formatted_top_collections = format_collections(top_collections, '30d')
    # print(json.dumps(formatted_top_collections, indent=2))

    # nft_metadata = await get_nft_metadata(network, contract_address, token_id)
    # print("NFT Metadata:")
    # print(json.dumps(nft_metadata, indent=8))
    


    # top_collections = await get_top_collections('7d', chains=['ethereum'], limit=10)
    # formatted_top_collections = format_collections(top_collections, '7d')
    # print(json.dumps(formatted_top_collections, indent=2))

    # trending_collections = await get_trending_collections('24h', chains=['ethereum'], limit=10)
    # formatted_trending_collections = format_collections(trending_collections, '24h')
    # print(json.dumps(formatted_trending_collections, indent=2))

    # metadata = await get_nft_metadata(network, contract_address, token_id)
    # print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    asyncio.run(main())