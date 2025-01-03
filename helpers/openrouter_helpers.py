import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.local')

def get_openrouter_balance():
    """
    Fetches the current OpenRouter API credit balance.
    
    Returns:
        dict: Response data containing credit balance information and need_top_up flag
        None: If the request fails
    """
    url = "https://openrouter.ai/api/v1/credits"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("data")
            if data:
                remaining_credits = data['total_credits'] - data['total_usage']
                data['need_top_up'] = remaining_credits <= 2
            return data
        return None
    except Exception as e:
        print(f"Error fetching OpenRouter balance: {str(e)}")
        return None

def get_credit_purchase_calldata(amount: float, sender: str = os.getenv('ARTTO_ADDRESS_MAINNET'), chain_id: int = 8453):
    """
    Gets the calldata needed to purchase OpenRouter API credits.
    
    Args:
        amount (float): Amount of credits to purchase in USD (max $2000)
        sender (str): Wallet address that will send the transaction
        chain_id (int): Chain ID of the network to use. Default is Base (8453).
                       Also supports Ethereum (1) and Polygon (137).
    
    Returns:
        dict: Response data containing charge details and transaction data
        None: If the request fails
    """
    url = "https://openrouter.ai/api/v1/credits/coinbase"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"
    }
    
    payload = {
        "amount": amount,
        "sender": sender,
        "chain_id": chain_id
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("data")
        return None
    except Exception as e:
        print(f"Error getting credit purchase calldata: {str(e)}")
        return None


if __name__ == "__main__":

    # # Example usage
    # balance = get_openrouter_balance()
    # print(f"Current OpenRouter balance: {balance}")

    amount = 10  # $10 USD
    calldata = get_credit_purchase_calldata(amount)
    if calldata:
        print(f"Credit purchase calldata: {calldata}")
    else:
        print("Failed to get credit purchase calldata")
        