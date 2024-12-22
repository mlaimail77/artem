import os
import requests
import json

# Mainnet = "ethereum",
# Polygon = "matic",
# Klaytn = "klaytn",
# Base = "base",
# Blast = "blast",
# Arbitrum = "arbitrum",
# ArbitrumNova = "arbitrum_nova",
# Avalanche = "avalanche",
# Optimism = "optimism",
# Solana = "solana",
# Zora = "zora",
# Sei = "sei",
# B3 = "b3",
# Sepolia = "sepolia",
# Amoy = "amoy",
# Baobab = "baobab",
# BaseSepolia = "base_sepolia",
# BlastSepolia = "blast_sepolia",
# ArbitrumSepolia = "arbitrum_sepolia",
# Fuji = "avalanche_fuji",
# OptimismSepolia = "optimism_sepolia",
# SolanaDevnet = "soldev",
# ZoraSepolia = "zora_sepolia",
# SeiTestnet = "sei_testnet",
# B3Sepolia = "b3_sepolia"


def make_opensea_offer(chain, token_address, token_id, amount, bearer_token):
    """
    Makes an offer on OpenSea through private endpoint
    
    Args:
        chain (str): Blockchain network (e.g. "Base")
        token_address (str): Contract address of the NFT
        token_id (str): Token ID of the NFT
        amount (str): Offer amount in WETH
        
    Returns:
        dict: Response from the OpenSea endpoint
    """
    endpoint = "http://artto-opensea:10000/make-offer"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "chain": chain,
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
