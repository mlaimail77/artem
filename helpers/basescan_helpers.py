import requests
import json
import os

from dotenv import load_dotenv

load_dotenv('.env.local')

def get_abi(network_id, contract_address):

    base_url = f"https://{'api-sepolia' if network_id == 'base-sepolia' else 'api'}.basescan.org/api"
    params = {
        "module": "contract",
        "action": "getabi", 
        "address": contract_address,
        "apikey": os.getenv('BASESCAN_API_KEY')
    }

    response = requests.get(base_url, params=params)
    response_json = response.json()

    if response_json["status"] == "1" and response_json["message"] == "OK":
        abi = json.loads(response_json["result"])
    else:
        abi = None
    return abi

def get_first_transaction_timestamp(wallet_address):
    """
    Fetches the timestamp of the first transaction for a given wallet address on Base
    
    Args:
        wallet_address (str): The wallet address to query
        
    Returns:
        int: Unix timestamp of first transaction, or None if no transactions found
    """
    base_url = "https://api.basescan.org/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": "0",
        "endblock": "99999999", 
        "page": "1",
        "offset": "1",
        "sort": "asc",
        "apikey": os.getenv('BASESCAN_API_KEY')
    }

    try:
        response = requests.get(base_url, params=params)
        response_json = response.json()

        if response_json["status"] == "1" and response_json["message"] == "OK":
            if len(response_json["result"]) > 0:
                return int(response_json["result"][0]["timeStamp"])
            return None
        return None
        
    except Exception as e:
        print(f"Error fetching first transaction timestamp: {str(e)}")
        return None
