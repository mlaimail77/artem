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

def purchase_openrouter_credits(amount_usd, bearer_token=os.getenv('OPENSEA_ARTTO_SERVER_BEARER_TOKEN'), endpoint=None):
    """
    Purchases OpenRouter credits.
    
    Args:
        amount_usd (int): Amount in USD to purchase
        
    Returns:
        dict: Response from the OpenSea endpoint
        None: If the request fails
    """
    if endpoint is None:
        endpoint = "https://artto-node-server.onrender.com/fund-openrouter"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "amount_usd": amount_usd
    }

    try:
        print("Making request to: ", endpoint)
        print("Headers: ", headers)
        print("Payload: ", payload)
        response = requests.post(endpoint, headers=headers, json=payload)
        print("Response: ", response)
        if response.status_code == 200:
            print(f"Successfully purchased {amount_usd} credits")
            return response.json()
        return None
    except Exception as e:
        print(f"Error purchasing OpenRouter credits: {str(e)}")
        return None


if __name__ == "__main__":

    # # Example usage
    balance = get_openrouter_balance()
    print(f"Current OpenRouter balance: {balance}")
    TOP_UP_AMOUNT = 10
    print("Need to top up OpenRouter balance")
    response = purchase_openrouter_credits(TOP_UP_AMOUNT, endpoint="http://localhost:3001/fund-openrouter")
    print(response)


        