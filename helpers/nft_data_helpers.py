import aiohttp
import json
import os
import asyncio
import requests

from dotenv import load_dotenv

load_dotenv('.env.local')

SIMPLEHASH_API_KEY = os.getenv('SIMPLEHASH_API_KEY')
OPENSEA_API_KEY = os.getenv('OPENSEA_API_KEY')

def get_twitter_from_opensea(response):
    if not response:
        print("No response from OpenSea API")
        return None
    if 'social_media_accounts' in response:
        for account in response['social_media_accounts']:
            if account['platform'] == 'twitter':
                return f"@{account['username']}"
    return None

def get_wallet_user_data(wallet_address: str, api_key: str = OPENSEA_API_KEY) -> dict:
    """
    Fetches user data for a wallet address using the OpenSea API.
    
    Args:
        wallet_address (str): The wallet address to lookup user data for
        api_key (str): The OpenSea API key to use. Default: OPENSEA_API_KEY
        
    Returns:
        dict: JSON response containing user data, or None if request fails
    """
    url = f"https://api.opensea.io/api/v2/accounts/{wallet_address}"
    
    headers = {
        "accept": "application/json",
        "x-api-key": api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def get_nfts_by_token_list(nft_ids: list, api_key: str = SIMPLEHASH_API_KEY) -> dict:
    """
    Fetches NFT data for a list of token IDs using the SimpleHash API.
    
    Args:
        nft_ids (list): List of NFT IDs in format "chain.contract_address.token_id"
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY
        
    Returns:
        dict: JSON response containing NFT data, or None if request fails
    """
    url = "https://api.simplehash.com/api/v0/nfts/assets"
    
    # Convert list to comma-separated string
    nft_ids_str = ",".join(nft_ids)
    
    params = {
        "nft_ids": nft_ids_str
    }

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def get_artto_balance(wallet_address: str, api_key: str = SIMPLEHASH_API_KEY) -> float:
    """
    Fetches $ARTTO token balance for a wallet address using SimpleHash API.
    
    Args:
        wallet_address (str): The wallet address to lookup balance for
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY
        
    Returns:
        float: $ARTTO token balance, or 0 if request fails or token not found
    """
    url = "https://api.simplehash.com/api/v0/fungibles/balances"
    
    params = {
        "chains": "base",
        "wallet_addresses": wallet_address,
        "include_fungible_details": 1,
        "include_prices": 1,
        "count": 0,
        "limit": 50,
        "include_native_tokens": 0
    }

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        for fungible in data.get("fungibles", []):
            if fungible.get("fungible_id") == "base.0x9239e9f9e325e706ef8b89936ece9d48896abbe3":
                return float(fungible.get("total_quantity_string", "0"))
    return 0

def get_wallet_collections(wallet_address: str, api_key: str = SIMPLEHASH_API_KEY, chains: str = "ethereum,base"):
    """
    Fetches NFT collections owned by a wallet address using the SimpleHash API.

    Args:
        wallet_address (str): The wallet address to lookup collections for
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY
        chains (str): Blockchain network to query. Default: "ethereum"

    Returns:
        dict: JSON response containing collection data, or None if request fails
    """
    url = f"https://api.simplehash.com/api/v0/nfts/collections_by_wallets_v2"
    
    params = {
        "chains": chains,
        "wallet_addresses": wallet_address,
        "nft_ids": 1,
        "include_escrowed_nfts": 0,
        "order_by": "transfer_time__desc",
        "limit": 50,
        "spam_score__lt": 90
    }

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def format_wallet_collections(response):
    collections = response["collections"]
    formatted_response = []
    for collection in collections:
        formatted_response.append({
            "name": collection.get("collection_details", {}).get("name") if collection.get("collection_details", {}).get("name") else None,
            "collection_id": collection.get("collection_details").get("collection_id") if collection.get("collection_details").get("collection_id") else None,
            "description": collection.get("collection_details", {}).get("description") if collection.get("collection_details", {}).get("description") else None,
            "category": collection.get("collection_details", {}).get("category") if collection.get("collection_details", {}).get("category") else None,
            "floor_prices": [{
                "marketplace": price.get("marketplace_name"),
                "value_eth": price.get("value", 0) / 1e18,
                "value_usd": price.get("value_usd_cents", 0) / 100
            } for price in collection.get("collection_details", {}).get("floor_prices", [])] if collection.get("collection_details", {}).get("floor_prices") else None,
            "top_bids": [{
                "marketplace": bid.get("marketplace_name"),
                "value_eth": bid.get("value", 0) / 1e18,
                "value_usd": bid.get("value_usd_cents", 0) / 100
            } for bid in collection.get("collection_details", {}).get("top_bids", [])] if collection.get("collection_details", {}).get("top_bids") else None,
            "distinct_owner_count": collection.get("collection_details", {}).get("distinct_owner_count") if collection.get("collection_details", {}).get("distinct_owner_count") else None,
            "distinct_nft_count": collection.get("collection_details", {}).get("distinct_nft_count") if collection.get("collection_details", {}).get("distinct_nft_count") else None,
            "total_quantity": collection.get("collection_details", {}).get("total_quantity") if collection.get("collection_details", {}).get("total_quantity") else None,
            "distinct_nfts_owned": collection.get("distinct_nfts_owned", {}),
            "total_copies_owned": collection.get("total_copies_owned", {}),
            "nft_ids": collection.get("nft_ids", [])
        })
    return formatted_response


def get_wallet_from_ens(ens_name: str, api_key: str = SIMPLEHASH_API_KEY) -> str:
    """
    Fetches the wallet address for an ENS name using the SimpleHash API.

    Args:
        ens_name (str): The ENS name to lookup
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY

    Returns:
        str: The wallet address if one exists, otherwise None
    """
    url = f"https://api.simplehash.com/api/v0/ens/lookup"
    
    params = {
        "ens_names": ens_name
    }

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            wallet = data[0].get("address")
            if wallet:
                return wallet
    return ens_name


def get_ens_name(wallet_address: str, api_key: str = SIMPLEHASH_API_KEY) -> str:
    """
    Fetches the ENS name for a wallet address using the SimpleHash API.

    Args:
        wallet_address (str): The wallet address to lookup
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY

    Returns:
        str: The ENS name if one exists, otherwise the wallet address
    """
    url = f"https://api.simplehash.com/api/v0/ens/reverse_lookup?wallet_addresses={wallet_address}"

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            ens = data[0].get("ens")
            if ens:
                return ens
    return wallet_address


def get_wallet_valuation(wallet_address: str, api_key: str = SIMPLEHASH_API_KEY):
    """
    Fetches the total NFT valuation for a specific wallet address from the SimpleHash API.

    Args:
        wallet_address (str): The wallet address to get valuation for
        api_key (str): The SimpleHash API key to use. Default: SIMPLEHASH_API_KEY

    Returns:
        float: The USD value of NFTs in the wallet, or None if request fails
    """
    url = f"https://api.simplehash.com/api/v0/nfts/owners/value?wallet_addresses={wallet_address}"

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data and "wallets" in data and len(data["wallets"]) > 0:
            return data["wallets"][0].get("usd_value")
    return None


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
        'nft_id': None if not response.get('nft_id') else response.get('nft_id'),
        'chain': None if not response.get('chain') else response.get('chain'),
        'contract_address': None if not response.get('contract_address') else response.get('contract_address'),
        'name': None if not response.get('name') else response.get('name'),
        'description': None if not response.get('description') else response.get('description'),
        'image_small_url': None if not response.get('previews', {}).get('image_small_url') else response.get('previews', {}).get('image_small_url'),
        'contract': None if not response.get('contract') else response.get('contract'),
        'collection_name': None if not response.get('collection', {}).get('name') else response.get('collection', {}).get('name'),
        'collection_id': None if not response.get('collection', {}).get('collection_id') else response.get('collection', {}).get('collection_id'),
        'floor_prices': [] if not response.get('collection', {}).get('floor_prices') else [{
            'marketplace': price.get('marketplace_name'),
            'value_eth': price.get('value', 0) / 1e18,
            'value_usd': price.get('value_usd_cents', 0) / 100
        } for price in response.get('collection', {}).get('floor_prices')],
        'collection_description': None if not response.get('collection', {}).get('description') else response.get('collection', {}).get('description'),
        'distinct_owner_count': None if not response.get('collection', {}).get('distinct_owner_count') else response.get('collection', {}).get('distinct_owner_count'),
        'distinct_nft_count': None if not response.get('collection', {}).get('distinct_nft_count') else response.get('collection', {}).get('distinct_nft_count'),
        'total_quantity': None if not response.get('collection', {}).get('total_quantity') else response.get('collection', {}).get('total_quantity'),
        'last_sale_usd': None if not response.get('last_sale', {}) else response.get('last_sale', {}).get('unit_price_usd_cents'),
        'first_created': None if not response.get('first_created') else response.get('first_created'),
        'rarity': None if not response.get('rarity') else response.get('rarity'),
        'attributes': None if not response.get('extra_metadata', {}).get('attributes') else response.get('extra_metadata', {}).get('attributes')
    }
    
    return filtered_response

def format_collections(response, time_period):
    collections = response["collections"]
    formatted_response = []
    for collection in collections:
        formatted_response.append({
            "name": collection.get("collection_details", {}).get("name") if collection.get("collection_details", {}).get("name") else None,
            "description": collection.get("collection_details", {}).get("description") if collection.get("collection_details", {}).get("description") else None,
            "chains": collection.get("collection_details", {}).get("chains") if collection.get("collection_details", {}).get("chains") else None,
            "category": collection.get("collection_details", {}).get("category") if collection.get("collection_details", {}).get("category") else None,
            "floor_prices": [{
                "marketplace": price.get("marketplace_name"),
                "value_eth": price.get("value", 0) / 1e18,
                "value_usd": price.get("value_usd_cents", 0) / 100
            } for price in collection.get("collection_details", {}).get("floor_prices", [])] if collection.get("collection_details", {}).get("floor_prices") else None,
            "distinct_owner_count": collection.get("collection_details", {}).get("distinct_owner_count") if collection.get("collection_details", {}).get("distinct_owner_count") else None,
            "distinct_nft_count": collection.get("collection_details", {}).get("distinct_nft_count") if collection.get("collection_details", {}).get("distinct_nft_count") else None,
            "total_quantity": collection.get("collection_details", {}).get("total_quantity") if collection.get("collection_details", {}).get("total_quantity") else None,
            "volume_percent_change": collection.get("volume_percent_change") if collection.get("volume_percent_change") else None,
            "transaction_count": collection.get("transaction_count") if collection.get("transaction_count") else None,
            "transaction_count_percent_change": collection.get("transaction_count_percent_change") if collection.get("transaction_count_percent_change") else None,
            "volume_usd": collection.get("volume_usd_cents")/100 if collection.get("volume_usd_cents") else None,
            "time_period": time_period if time_period else None
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
                formatted = filter_nft_metadata(response_data)
                return formatted
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