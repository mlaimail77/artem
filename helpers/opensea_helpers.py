import os
import requests
import json

CHAIN_IDS = {
    "ethereum": "Ethereum",
    "matic": "Polygon",
    "klaytn": "Klaytn", 
    "base": "Base",
    "blast": "Blast",
    "arbitrum": "Arbitrum",
    "arbitrum_nova": "ArbitrumNova",
    "avalanche": "Avalanche",
    "optimism": "Optimism",
    "solana": "Solana",
    "zora": "Zora",
    "sei": "Sei",
    "b3": "B3",
    "sepolia": "Sepolia",
    "amoy": "Amoy",
    "baobab": "Baobab",
    "base_sepolia": "BaseSepolia",
    "blast_sepolia": "BlastSepolia",
    "arbitrum_sepolia": "ArbitrumSepolia",
    "avalanche_fuji": "Fuji",
    "optimism_sepolia": "OptimismSepolia",
    "soldev": "SolanaDevnet",
    "zora_sepolia": "ZoraSepolia",
    "sei_testnet": "SeiTestnet",
    "b3_sepolia": "B3Sepolia"
}

def make_opensea_listing(chain, token_address, token_id, amount, bearer_token, endpoint=None):
    """
    Creates a listing on OpenSea through private endpoint
    
    Args:
        chain (str): Blockchain network (e.g. "Base") 
        token_address (str): Contract address of the NFT
        token_id (str): Token ID of the NFT
        amount (str): Listing price in ETH
        bearer_token (str): Bearer token for authentication
        endpoint (str): Optional endpoint to use instead of default
    Returns:
        dict: Response from the OpenSea endpoint
    """
    amount = max(0.00001, float(amount))
    amount = "{:.5f}".format(amount).rstrip('0')
    if endpoint is None:
        endpoint = "http://artto-opensea:10000/create-listing"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    # Look up chain ID if not in mapping
    chain_id = CHAIN_IDS.get(chain.lower(), chain)
    
    payload = {
        "chain": chain_id,
        "tokenAddress": token_address,
        "tokenId": token_id, 
        "startAmount": amount
    }
    
    print("Sending payload: ", payload)
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def make_opensea_auction(chain, token_address, token_id, amount, bearer_token, endpoint=None):
    """
    Creates an auction listing on OpenSea through private endpoint
    
    Args:
        chain (str): Blockchain network (e.g. "Base")
        token_address (str): Contract address of the NFT
        token_id (str): Token ID of the NFT
        amount (str): Starting bid amount in ETH
        bearer_token (str): Bearer token for authentication
        endpoint (str): Optional endpoint to use instead of default
    Returns:
        dict: Response from the OpenSea endpoint
    """
    if float(amount) > 0:
        amount = max(0.00001, float(amount))
        amount = "{:.5f}".format(amount).rstrip('0')

    if endpoint is None:
        endpoint = "http://artto-opensea:10000/create-auction"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    # Look up chain ID if not in mapping
    chain_id = CHAIN_IDS.get(chain.lower(), chain)
    
    payload = {
        "chain": chain_id,
        "tokenAddress": token_address,
        "tokenId": token_id,
        "startAmount": amount,
    }
    
    print("Sending payload: ", payload)
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print("Response from OpenSea: ", response.json())
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def make_opensea_offer(chain, token_address, token_id, amount, bearer_token, endpoint=None):
    """
    Makes an offer on OpenSea through private endpoint
    
    Args:
        chain (str): Blockchain network (e.g. "Base")
        token_address (str): Contract address of the NFT
        token_id (str): Token ID of the NFT
        amount (str): Offer amount in WETH
        bearer_token (str): Bearer token for authentication
        endpoint (str): Optional endpoint to use instead of default
    Returns:
        dict: Response from the OpenSea endpoint
    """
    if endpoint is None:
        endpoint = "http://artto-opensea:10000/make-offer"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    # Look up chain ID if not in mapping
    chain_id = CHAIN_IDS.get(chain.lower(), chain)
    
    payload = {
        "chain": chain_id,
        "tokenAddress": token_address, 
        "tokenId": token_id,
        "amount": amount
    }
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
