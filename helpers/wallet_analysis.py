from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.image_processing_helpers import *

from datetime import timezone, timedelta

import base64
import time
import uuid
import random

from dotenv import load_dotenv

load_dotenv('.env.local')

def get_wallet_info(wallet_address):

    # Resolve wallet address if it's an ENS name
    if not wallet_address.startswith('0x'):
        wallet_address = get_wallet_from_ens(wallet_address)

    collections = get_wallet_collections(wallet_address)
    formatted_collections = format_wallet_collections(collections)
    
    # Sort collections by highest floor price (USD) across any marketplace
    sorted_collections = sorted(
        formatted_collections,
        key=lambda x: max([price['value_usd'] for price in x['top_bids']]) if x['top_bids'] else 0,
        reverse=True
    )
    
    # Get top 15 collections by value
    most_valuable_collections = sorted_collections[:15]

    # Get 5 random collections
    random_collections = random.sample(formatted_collections, 5)
    # Initialize arrays for NFTs to analyze
    valuable_nfts_to_analyze = []
    random_nfts_to_analyze = []
    
    # Sample one random NFT from each valuable collection's nft_ids
    for collection in most_valuable_collections:
        if collection['nft_ids']:
            random_nft = random.choice(collection['nft_ids'])
            valuable_nfts_to_analyze.append(random_nft)
    
    # Sample one random NFT from each recent collection's nft_ids 
    for collection in random_collections:
        if collection['nft_ids']:
            random_nft = random.choice(collection['nft_ids'])
            random_nfts_to_analyze.append(random_nft)
    
    # Get NFT data for both sets
    valuable_nft_data = get_nfts_by_token_list(valuable_nfts_to_analyze)['nfts']
    random_nft_data = get_nfts_by_token_list(random_nfts_to_analyze)['nfts']

    # Map NFT images to their collection IDs for both valuable and recent collections
    for nft in valuable_nft_data + random_nft_data:
        for collection in most_valuable_collections + random_collections:
            if nft["collection"]["collection_id"] == collection.get("collection_id"):
                collection["nft_description"] = nft.get("description", "")
                collection["image_small_url"] = nft.get("previews", {}).get("image_small_url", "")
                collection["image_medium_url"] = nft.get("previews", {}).get("image_medium_url", "")
                collection["user_purchase_price_usd"] = nft.get("last_sale", {}).get("unit_price_usd_cents", 1) / 100 if nft.get("last_sale", {}) else 0
                collection["user_purchase_timestamp"] = nft.get("last_sale", {}).get("timestamp", "") if nft.get("last_sale", {}) else ""
                collection["first_sale_price_usd"] = nft.get("primary_sale", {}).get("unit_price_usd_cents", 1) / 100 if nft.get("primary_sale", {}) else 0
                collection["first_sale_timestamp"] = nft.get("primary_sale", {}).get("timestamp", "") if nft.get("primary_sale", {}) else ""
                break

    # Select 4 NFTs for visualization
    image_urls = []
    
    # Add 4 from most valuable if available
    for collection in most_valuable_collections[:4]:
        if collection.get("image_small_url"):
            image_urls.append({
                "url": collection["image_small_url"],
                "name": collection.get("name", "Unnamed NFT")
            })
            
    # Twitter username
    user_data = get_wallet_user_data(wallet_address)
    twitter_username = get_twitter_from_opensea(user_data)
    print("Twitter username: ", twitter_username)

    wallet_data = {
        "wallet_address": wallet_address,
        "most_valuable_collections": most_valuable_collections,
        "random_collections": random_collections,
        "twitter_username": twitter_username,
        "image_urls": image_urls
    }

    return wallet_data


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_analysis(wallet_data, tone, current_valuation):
    image_urls = wallet_data["image_urls"]

    # Combine images
    # Generate and save combined image to temp file
    combined_image = combine_images(image_urls)
    temp_image_path = f"temp_wallet_analysis_{uuid.uuid4()}.jpg"
    combined_image.save(temp_image_path)

    # Get base64 encoded image
    base64_image = encode_image(temp_image_path)

    roast = get_wallet_analysis_text(wallet_data, base64_image, tone, current_valuation)

    # Clean up temp file
    os.remove(temp_image_path)

    response = {
        "analysis": roast,
        "image_urls": image_urls
    }

    return response