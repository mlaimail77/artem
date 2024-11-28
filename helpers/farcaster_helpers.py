import os
import requests
from dotenv import load_dotenv # can be installed with `pip install python-dotenv`

load_dotenv('.env.local')

NEYNAR_API_KEY = os.getenv('NEYNAR_API_KEY')
SIGNER_UUID = os.getenv('SIGNER_UUID')

def post_cast(text, parent=None, channel_id=None):
    url = "https://api.neynar.com/v2/farcaster/cast"
    
    payload = {
        "signer_uuid": SIGNER_UUID,
        "text": text
    }
    
    if parent:
        payload["parent"] = parent
        
    if channel_id:
        payload["channel_id"] = channel_id

    headers = {
        "accept": "application/json", 
        "content-type": "application/json",
        "x-api-key": NEYNAR_API_KEY
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def search_casts(query, limit=25):
    url = f"https://api.neynar.com/v2/farcaster/cast/search?q={query}&priority_mode=false&limit={limit}"
    
    headers = {
        "accept": "application/json",
        "x-api-key": NEYNAR_API_KEY
    }

    response = requests.get(url, headers=headers)
    return response.json()

def get_casts(identifier):
    url = f"https://api.neynar.com/v2/farcaster/cast?identifier={identifier}&type=hash"
    
    headers = {
        "accept": "application/json",
        "x-api-key": NEYNAR_API_KEY
    }

    response = requests.get(url, headers=headers)
    return response.json()
