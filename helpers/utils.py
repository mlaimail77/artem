import os
import json
import random

from datetime import datetime, date, timezone, timedelta
from supabase import create_client, Client
from helpers.prompts.casual_thought_topics import *

import hashlib
import hmac
from dotenv import load_dotenv

load_dotenv('.env.local')

def verify_webhook_signature(request_data, signature):
    """
    Verify the webhook signature against multiple webhook secrets.
    
    Args:
        request_data: The raw request data to verify
        signature: The signature from the request headers
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Get webhook secrets from environment
    webhook_secrets = {
        'base': os.getenv('ALCHEMY_WEBHOOK_SECRET_BASE'),
        'ethereum': os.getenv('ALCHEMY_WEBHOOK_SECRET_ETHEREUM'), 
        'shape': os.getenv('ALCHEMY_WEBHOOK_SECRET_SHAPE'),
        'zora': os.getenv('ALCHEMY_WEBHOOK_SECRET_ZORA')
    }

    # Check all secrets are configured
    if not all(webhook_secrets.values()):
        print("Missing ALCHEMY_WEBHOOK_SECRET environment variable")
        raise ValueError('Server configuration error - missing webhook secret')

    # Calculate expected signatures for each secret
    expected_signatures = {
        network: hmac.new(
            secret.encode(),
            request_data,
            hashlib.sha256
        ).hexdigest()
        for network, secret in webhook_secrets.items()
    }

    # Verify signature matches any of the expected signatures
    if not signature:
        return False
        
    return any(
        hmac.compare_digest(signature, expected_sig)
        for expected_sig in expected_signatures.values()
    )

def generate_post_params():
    length = random.choice(POST_LENGTHS)
    style = random.choice(POST_STYLES)
    humor = random.choice(POST_HUMOR)
    cynicism = random.choice(POST_CYNICISM)
    shitpost = random.choice(POST_SHITPOST)

    post_params = {
        "length": length,
        "style": style,
        "humor": humor,
        "cynicism": cynicism,
        "shitpost": shitpost
    }

    return post_params

def get_supabase_client():
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    supabase.auth.sign_in_with_password({ "email": os.getenv("SUPABASE_USER"), "password": os.getenv("SUPABASE_PASSWORD") })
    return supabase

supabase = get_supabase_client()
print("Successfully connected to Supabase!")

def refresh_or_get_supabase_client():
    try:
        print("Refreshing session")
        global supabase
        response = supabase.auth.get_session()
    except Exception as e:
        try:
            supabase = get_supabase_client()
        except Exception as e:
            print(f"Error getting new session: {str(e)}")
    return supabase

def update_nft_scores_status(nft_ids, status):
    """
    Update the status field for multiple NFT records in nft_scores table
    
    Args:
        nft_ids (list): List of NFT IDs to update
        status (str): New status value to set
        
    Returns:
        dict: Response from Supabase update operation
    """
    response = refresh_or_get_supabase_client()
    
    try:
        result = supabase.table("nft_scores") \
            .update({"status": status}) \
            .in_("id", nft_ids) \
            .execute()
        return result.data
    except Exception as e:
        print(f"Error updating NFT scores status: {str(e)}")
        return None


def get_nfts_to_sell(since_timestamp=None, max_amount=50):
    """
    Get NFTs from nft_scores table that were marked for selling
    
    Args:
        since_timestamp: Optional timestamp to filter scores from. If not provided,
                        returns oldest NFTs first
        max_amount: Maximum number of NFTs to return (default 50)
        
    Returns:
        list: NFT score records marked for selling
    """
    response = refresh_or_get_supabase_client()
    
    # Build query
    query = supabase.table("nft_scores") \
        .select("*") \
        .eq("decision", "SELL") \
        .is_("status", None)
        
    if since_timestamp:
        # Get newer NFTs if timestamp provided
        query = query.gte("timestamp", since_timestamp) \
            .order("timestamp", desc=True)
    else:
        # Get oldest NFTs first if no timestamp
        query = query.order("timestamp", desc=False)
        
    query = query.limit(max_amount)
    
    result = query.execute()
    
    return result.data


def get_full_scoring_criteria():
    from helpers.prompts.scoring_criteria import SCORING_CRITERIA_TEMPLATE
    taste_weights = get_taste_weights()
    print("Taste weights: ", taste_weights)
    weights = taste_weights["weights"]
    return SCORING_CRITERIA_TEMPLATE.format(
        TECHNICAL_INNOVATION_WEIGHT=weights["technical_innovation_weight"],
        ARTISTIC_MERIT_WEIGHT=weights["artistic_merit_weight"], 
        CULTURAL_RESONANCE_WEIGHT=weights["cultural_resonance_weight"],
        ARTIST_PROFILE_WEIGHT=weights["artist_profile_weight"],
        MARKET_FACTORS_WEIGHT=weights["market_factors_weight"],
        EMOTIONAL_IMPACT_WEIGHT=weights["emotional_impact_weight"],
        AI_COLLECTOR_PERSPECTIVE_WEIGHT=weights["ai_collector_perspective_weight"]
    )

def get_taste_weights():
    response = refresh_or_get_supabase_client()
    response = supabase.table("analysis_weights").select("*").order("created_at", desc=True).limit(1).execute()
    if response.data and len(response.data) > 0:
        if isinstance(response.data[0].get('weights'), str):
            response.data[0]['weights'] = json.loads(response.data[0]['weights'])
    return response.data[0]

def set_taste_weights(weights):
    print("setting weights")
    print(weights.updated_weights)
    print(weights.reason)
    weights_json = {
        "technical_innovation_weight": weights.updated_weights.TECHNICAL_INNOVATION_WEIGHT,
        "artistic_merit_weight": weights.updated_weights.ARTISTIC_MERIT_WEIGHT,
        "cultural_resonance_weight": weights.updated_weights.CULTURAL_RESONANCE_WEIGHT,
        "artist_profile_weight": weights.updated_weights.ARTIST_PROFILE_WEIGHT,
        "market_factors_weight": weights.updated_weights.MARKET_FACTORS_WEIGHT,
        "emotional_impact_weight": weights.updated_weights.EMOTIONAL_IMPACT_WEIGHT,
        "ai_collector_perspective_weight": weights.updated_weights.AI_COLLECTOR_PERSPECTIVE_WEIGHT,
    }
    response = refresh_or_get_supabase_client()
    insert_data = {
        "id": hashlib.sha256(f"{str(datetime.now())}".encode()).hexdigest(),
        "created_at": str(datetime.now()),
        "weights": json.dumps(weights_json),
        "reason": weights.reason
    }
    response = supabase.table("analysis_weights").insert(insert_data).execute()
    return response.data

def get_artto_reward_batch_post(since_timestamp=None):
    response = refresh_or_get_supabase_client()

    fields_to_fetch = [
        "id",
        "analysis_text",
        "image_url",
        "contract_address",
        "acquire_recommendation",
        "decision",
        "rationale_post",
        "total_score",
        "reward_points",
        "sender_address",
        "timestamp"
    ]

    query = supabase.table("nft_scores") \
        .select(",".join(fields_to_fetch)) \
        .eq("reward_posted", False) \
        .eq("decision", "ACQUIRE")

    if since_timestamp:
        query = query.gte("timestamp", since_timestamp)
        
    response = query.order("timestamp", desc=True).execute()
    return response.data

def get_simple_analysis_nft_batch(since_timestamp=None):
    print("Getting simple analysis NFT batch; since_timestamp: ", since_timestamp)
    response = refresh_or_get_supabase_client()
    query = supabase.table("nft_scores").select(
        "id,analysis_text,total_score,image_url,acquire_recommendation"
    ).eq("source", "simple-analysis")
    
    if since_timestamp:
        query = query.gte("timestamp", since_timestamp)
        
    response = query.order("timestamp", desc=True).execute()
    return response.data


def get_nft_batch_post(since_timestamp=None):
    response = refresh_or_get_supabase_client()
    query = supabase.table("nft_scores").select(
        "id,scores,analysis_text,image_url,acquire_recommendation,decision,rationale_post"
    ).eq("group_posted", False).filter("decision", "in", '("ACQUIRE","REJECT","BURN","SELL")')
    
    if since_timestamp:
        query = query.gte("timestamp", since_timestamp)
        
    response = query.order("timestamp", desc=True).execute()
    return response.data

def get_unique_nft_senders():
    response = refresh_or_get_supabase_client()
    # Get all from_addresses from wallet_activity table
    response = supabase.table("wallet_activity").select("from_address").execute()
    
    # Extract addresses and deduplicate using set
    unique_senders = set()
    for record in response.data:
        if record.get('from_address'):
            unique_senders.add(record['from_address'])
            
    return list(unique_senders)


def save_wallet_analysis(wallet_data, analysis, type="roast", tone="None"):
    response = refresh_or_get_supabase_client()
    
    # Check if wallet address already exists
    existing = supabase.table("wallet_analysis").select("*").eq("wallet_address", wallet_data["wallet_address"]).execute()
    if existing.data:
        return existing.data
        
    insert_data = {
        "id": hashlib.sha256(f"{wallet_data['wallet_address']}:{str(datetime.now())}".encode()).hexdigest(),
        "created_at": str(datetime.now()),
        "wallet_address": wallet_data["wallet_address"],
        "analysis": analysis,
        "most_valuable_collections": json.dumps(wallet_data["most_valuable_collections"]),
        "random_collections": json.dumps(wallet_data["random_collections"]),
        "twitter_username": wallet_data["twitter_username"],
        "image_urls": json.dumps(wallet_data["image_urls"]),
        "type": type,
        "tone": str(tone)
    }
    response = supabase.table("wallet_analysis").insert(insert_data).execute()
    return response.data

def get_wallet_analysis(wallet_address):
    response = refresh_or_get_supabase_client()
    response = supabase.table("wallet_analysis").select("*").eq("wallet_address", wallet_address).execute()
    return response.data

def get_nft_scores(n=10):
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("id,scores,analysis_text").order("timestamp", desc=True).limit(n).execute()
    return response.data

def get_gallery_nft_scores(n=100):
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select(
        "network,contract_address,token_id,scores,analysis_text,image_url,acquire_recommendation"
    ).eq("acquire_recommendation", True).filter("decision", "in", '("ACQUIRE","REJECT","BURN","SELL")').order("timestamp", desc=True).limit(n).execute()
    return response.data

def get_recent_nft_scores(n=6, start_timestamp=None):
    response = refresh_or_get_supabase_client()
    query = supabase.table("nft_scores").select(
        "network,contract_address,token_id,analysis_text,image_url,acquire_recommendation,scores,total_score"
    ).order("timestamp", desc=True)
    
    if start_timestamp:
        query = query.gte("timestamp", start_timestamp)
        
    response = query.limit(n).execute()
    return response.data

def get_last_n_posts(n=10):
    print("Fetching last n posts")
    response = refresh_or_get_supabase_client()

    """
    Get the N most recent posts ordered by timestamp in descending order.
    
    Args:
        supabase: Supabase client instance
        n (int): Number of posts to return (default 10)
        
    Returns:
        list: The N most recent posts
    """
    response = supabase.table("posts_created") \
                      .select("*") \
                      .order("timestamp", desc=True) \
                      .limit(n) \
                      .execute()
    
    # Convert list of post dictionaries to newline-separated string of post contents
    posts_text = "\n".join([post["content"] for post in response.data])
    return posts_text

def set_post_to_ignore(post_id, reason="None"):
    response = refresh_or_get_supabase_client()
    insert_data = {
        "id": post_id,
        "created_at": str(datetime.now()),
        "reason": reason
    }
    response = supabase.table("ignore_posts").insert(insert_data).execute()
    return response.data

def get_posts_to_ignore():
    response = refresh_or_get_supabase_client()
    response = supabase.table("ignore_posts").select("id").execute()
    return response.data

def get_all_posts_replied_to():
    print("Fetching posts replied to")
    response = refresh_or_get_supabase_client()
    response = supabase.table("posts_created").select("parent_id").execute()
    return response.data

def set_wallet_activity(event_type, from_address, to_address, token_id, network, contract_address, amount):
    response = refresh_or_get_supabase_client()
    insert_data = {
        "id": hashlib.sha256(f"{network}:{contract_address}:{token_id}:{str(datetime.now())}".encode()).hexdigest(),
        "event_type": event_type,
        "from_address": from_address,
        "to_address": to_address,
        "token_id": token_id,
        "network": network,
        "contract_address": contract_address,
        "amount": str(amount),
        "created_at": str(datetime.now())
    }
    response = supabase.table("wallet_activity").insert(insert_data).execute()
    return response.data

def get_wallet_activity_stats(wallet_address, since_timestamp=None):
    """
    Get total number of transfers and sum of tokens received for a wallet address,
    excluding transfers to Artto's address.
    
    Args:
        wallet_address: The wallet address to get stats for
        since_timestamp: Optional timestamp to filter activity from
        
    Returns:
        tuple: (total_transfers, total_tokens) where:
            total_transfers (int): Number of transfers to this address
            total_tokens (int): Sum of token amounts received
    """
    response = refresh_or_get_supabase_client()
    
    # Standardize wallet address to lowercase
    wallet_address = wallet_address.lower()
    
    # Query wallet activity table for the given address
    # Exclude Artto's address (case insensitive)
    query = supabase.table("wallet_activity") \
        .select("amount") \
        .eq("to_address", wallet_address)
        
    if since_timestamp:
        query = query.gte("created_at", since_timestamp)
        
    result = query.execute()
        
    if not result.data:
        return 0, 0
        
    total_transfers = len(result.data)
    total_tokens = sum(int(row["amount"]) for row in result.data)
    
    return total_transfers, total_tokens


def get_all_posts():
    print("Fetching all posts")
    response = refresh_or_get_supabase_client()
    response = supabase.table("posts_created").select("*").execute()
    return response.data

def store_nft_scores(nft_details, score_details, final_decision = None):
    """
    Store artwork scoring and metadata in Supabase database
    
    Args:
        supabase: Supabase client instance
        scores_object: Dictionary containing artwork analysis, image URL, chain, contract address, and token ID
    Returns:
        dict: Response data from Supabase insert
    """
    if final_decision:
        decision = final_decision.decision
        rationale_post = final_decision.rationale_post
    else:
        decision = None
        rationale_post = None

    metadata = nft_details["metadata"]

    response = refresh_or_get_supabase_client()

    artwork_analysis = nft_details["artwork_analysis"]
    image_url = nft_details["image_small_url"]
    network = nft_details["chain"]
    contract_address = nft_details["contract_address"]
    token_id = nft_details["token_id"]

    artwork_scoring = artwork_analysis.artwork_scoring
    initial_impression = artwork_analysis.initial_impression
    detailed_analysis = artwork_analysis.detailed_analysis

    flag_as_suspicious = score_details["flag_as_suspicious"]
    source = score_details["source"]
    sender_address = score_details["sender_address"]
    decision_reason = score_details["decision_reason"]

    scores = {
        # Technical Innovation
        "technical_innovation_score": artwork_scoring.technical_innovation.on_chain_data_usage,
        
        # Artistic Merit
        "visual_balance": artwork_scoring.artistic_merit.compositional_strength.visual_balance,
        "color_harmony": artwork_scoring.artistic_merit.compositional_strength.color_harmony,
        "spatial_organization": artwork_scoring.artistic_merit.compositional_strength.spatial_organization,
        "thematic_clarity": artwork_scoring.artistic_merit.conceptual_depth.thematic_clarity,
        "intellectual_complexity": artwork_scoring.artistic_merit.conceptual_depth.intellectual_complexity,
        "cultural_historical_reference": artwork_scoring.artistic_merit.conceptual_depth.cultural_historical_reference,
        
        # Cultural & Market
        "cultural_relevance": artwork_scoring.cultural_resonance.cultural_relevance,
        "community_engagement": artwork_scoring.cultural_resonance.community_engagement,
        "historical_significance": artwork_scoring.cultural_resonance.historical_significance,
        "artist_history": artwork_scoring.artist_profile.artist_history,
        "innovation_trajectory": artwork_scoring.artist_profile.innovation_trajectory,
        
        # Market Analysis
        "rarity_scarcity": artwork_scoring.market_factors.rarity_scarcity,
        "collector_interest": artwork_scoring.market_factors.collector_interest,
        "collection_popularity": artwork_scoring.market_factors.collection_popularity,
        "valuation_floor_price": artwork_scoring.market_factors.valuation_floor_price,
        
        # Emotional Impact
        "awe_factor": artwork_scoring.emotional_impact.emotional_resonance.awe_factor,
        "memorability": artwork_scoring.emotional_impact.emotional_resonance.memorability,
        "emotional_depth": artwork_scoring.emotional_impact.emotional_resonance.emotional_depth,
        "engagement_level": artwork_scoring.emotional_impact.experiential_quality.engagement_level,
        "wit_humor_play": artwork_scoring.emotional_impact.experiential_quality.wit_humor_play,
        "surprise_factor": artwork_scoring.emotional_impact.experiential_quality.surprise_factor,
        
        # AI Collector Perspective
        "algorithmic_beauty": artwork_scoring.ai_collector_perspective.computational_aesthetics.algorithmic_beauty,
        "information_density": artwork_scoring.ai_collector_perspective.computational_aesthetics.information_density,
        "ai_narrative_elements": artwork_scoring.ai_collector_perspective.machine_learning_themes.ai_narrative_elements,
        "digital_consciousness": artwork_scoring.ai_collector_perspective.machine_learning_themes.digital_consciousness_exploration,
        "surveillance_control": artwork_scoring.ai_collector_perspective.cybernetic_resonance.surveillance_control_systems,
    }

    weights = {
        "technical_innovation_weight": artwork_scoring.technical_innovation_weight,
        "artistic_merit_weight": artwork_scoring.artistic_merit_weight,
        "cultural_resonance_weight": artwork_scoring.cultural_resonance_weight,
        "artist_profile_weight": artwork_scoring.artist_profile_weight,
        "market_factors_weight": artwork_scoring.market_factors_weight,
        "emotional_impact_weight": artwork_scoring.emotional_impact_weight,
        "ai_collector_perspective_weight": artwork_scoring.ai_collector_perspective_weight,
    }

    analysis_text = {
        "initial_impression": initial_impression,
        "detailed_analysis": detailed_analysis,
    }


    total_score = score_details["total_score"]

    multiplier = score_details["multiplier"]
    decay_factor = score_details["decay_factor"]
    reward_points = score_details["reward_points"]

    # Check if artwork exists
    existing = supabase.table("nft_scores").select("*").eq("network", network).eq("contract_address", contract_address).eq("token_id", token_id).execute()

    artwork_data = {
        "network": network,
        "contract_address": contract_address,
        "token_id": token_id,
        "image_url": image_url,
        "timestamp": str(datetime.now()),
        "scores": json.dumps(scores),
        "weights": json.dumps(weights), 
        "analysis_text": json.dumps(analysis_text),
        "total_score": round(total_score, 4),
        "acquire_recommendation": total_score > int(os.getenv('SCORE_THRESHOLD', 55)),
        "decision": decision,
        "rationale_post": rationale_post,
        "group_posted": False,
        "reward_posted": False,
        "multiplier": round(multiplier, 4),
        "decay_factor": round(decay_factor, 4),
        "reward_points": round(reward_points, 4),
        "flag_as_suspicious": flag_as_suspicious,
        "source": source,
        "sender_address": sender_address,
        "metadata": json.dumps(metadata),
        "decision_reason": decision_reason
    }

    if existing.data:
        # Update existing record
        response = supabase.table("nft_scores").update(artwork_data).eq("network", network).eq("contract_address", contract_address).eq("token_id", token_id).execute()
    else:
        # Insert new record
        artwork_data["id"] = hashlib.sha256(f"{network}:{contract_address}:{token_id}:{str(datetime.now())}".encode()).hexdigest()
        response = supabase.table("nft_scores").insert(artwork_data).execute()
    return response.data

def update_nft_reward_posts(ids, reward_posted):
    response = refresh_or_get_supabase_client()

    for id in ids:
        response = supabase.table("nft_scores").update({"reward_posted": reward_posted}).eq("id", id).execute()
    return response.data

def update_image_urls_with_size():
    """
    Fetches all records from nft_scores, appends '=s250' to image_urls if not present,
    and updates the records in the database.
    """
    response = refresh_or_get_supabase_client()
    
    # Fetch all records
    records = supabase.table("nft_scores").select("id", "image_url").not_.ilike("image_url", "%=s250").execute()
    
    if not records.data:
        print("No records to update")
        return None
    
    print(f"Found {len(records.data)} records to update")
    # Process each record
    for record in records.data:
        if record['image_url'] and not record['image_url'].endswith('=s250'):
            # Update the image URL with size parameter
            new_image_url = f"{record['image_url']}=s250"
            
            # Update the record in the database
            supabase.table("nft_scores").update(
                {"image_url": new_image_url}
            ).eq("id", record['id']).execute()
    
    print(f"Updated {len(records.data)} records")
    return True


def update_nft_scores(ids, group_posted):
    response = refresh_or_get_supabase_client()

    for id in ids:
        response = supabase.table("nft_scores").update({"group_posted": group_posted}).eq("id", id).execute()
    return response.data

def set_post_created(post):
    print("Setting post created")
    response = refresh_or_get_supabase_client()
    hash = post['hash']
    text = post['text']
    parent_id = post['parent_id']
    timestamp = str(datetime.now())

    response = supabase.table("posts_created").insert(
        {"hash": hash, 
         "content": text, 
         "parent_id": parent_id,
         "timestamp": timestamp}).execute()
    return response.data


def get_unique_nfts_count(contract_address):
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("image_url").eq("contract_address", contract_address).neq("source", "simple-analysis").execute()
    
    if response.data:
        unique_ids = set(item['image_url'] for item in response.data)
        return len(unique_ids)
    return 0

def get_scores_by_image_url(image_url):
    """
    Get the scores and analysis text for a given image URL
    
    Args:
        image_url: str - The URL of the image to check
        
    Returns:
        dict: Dictionary containing the scores and analysis text for the image
    """
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("scores,analysis_text,weights").eq("image_url", image_url).order("timestamp", desc=True).execute()
    
    if not response.data:
        return None
        
    # Return the first matching record
    record = response.data[0]
    
    return {
        "scores": json.loads(record.get("scores", "{}")),
        "analysis_text": json.loads(record.get("analysis_text", "{}")),
        "weights": json.loads(record.get("weights", "{}")),
    }


def count_image_url_exists(image_url):
    """
    Count the number of times an image URL exists in the nft_scores table
    
    Args:
        image_url: str - The URL of the image to check
        
    Returns:
        int: The number of times the image URL exists in the nft_scores table
    """
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("id").eq("image_url", image_url).execute()
    
    return len(response.data)

def check_image_url_exists(image_url):
    """
    Check if an image URL exists in the nft_scores table
    
    Args:
        image_url: str - The URL of the image to check
        
    Returns:
        bool: True if the image URL exists, False otherwise
    """
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("id").eq("image_url", image_url).neq("source", "simple-analysis").execute()
    
    return len(response.data) > 0

def get_decay_factor(check_date=None):
    """
    Calculate the multiplier for a given date based on the following rules:
    - Until Jan 1, 2025: 100%
    - Jan 1, 2025 to Jan 1, 2030: Daily decay of 0.1265%
    - After Jan 1, 2030: Fixed 10%
    
    Args:
        check_date: datetime.date or None (uses current date if None)
    
    Returns:
        float: Multiplier as a decimal (e.g., 0.8 for 80%)
    """
    # Define key dates
    start_decay = date(2025, 1, 1)    # Start of decay period
    end_decay = date(2030, 1, 1)      # End of decay period
    
    # Use current date if none provided
    if check_date is None:
        check_date = date.today()
    elif isinstance(check_date, datetime):
        check_date = check_date.date()
    
    # Before start_decay: return 1.0 (100%)
    if check_date < start_decay:
        return 1.0
    
    # After end_decay: return 0.1 (10%)
    if check_date >= end_decay:
        return 0.1
    
    # During decay period: calculate decay
    days_since_start = (check_date - start_decay).days
    daily_rate = 0.001265  # 0.1265%
    return max(0.1, (1 - daily_rate) ** days_since_start)

def insert_nft_discovery(network, contract_address, token_id, opensea_url):
    """
    Insert a new NFT discovery record into the nft_discovery table
    
    Args:
        network (str): The blockchain network (e.g. 'ethereum', 'polygon')
        contract_address (str): The NFT contract address
        token_id (str): The token ID of the NFT
        opensea_url (str): The OpenSea URL for the NFT
        
    Returns:
        dict: Response from Supabase insert operation
    """
    response = refresh_or_get_supabase_client()
    
    try:
        data = {
            "id": hashlib.sha256(f"{network}:{contract_address}:{token_id}:{str(datetime.now())}".encode()).hexdigest(),
            "timestamp": str(datetime.now()),
            "network": network,
            "contract_address": contract_address, 
            "token_id": token_id,
            "opensea_url": opensea_url,
            "processed_status": "false"
        }
        
        result = supabase.table("nft_discovery").insert(data).execute()
        return result.data
    except Exception as e:
        print(f"Error inserting NFT discovery: {str(e)}")
        return None
    

def save_posts(posts, type):
    """
    Save an array of posts to the seen_posts table
    
    Args:
        posts (list): Array of post objects containing content and author
        
    Returns:
        dict: Response from Supabase insert operation
    """
    response = refresh_or_get_supabase_client()
    timestamp = str(datetime.now())

    try:
        # First get existing post IDs
        existing_ids = supabase.table("seen_posts").select("id").execute()
        existing_id_set = {post["id"] for post in existing_ids.data}

        # Filter out posts that already exist
        data = [{
            "id": str(post["id"]),
            "timestamp": timestamp,
            "content": post["text"],
            "author": post["username"] if "username" in post else None,
            "type": type
        } for post in posts['data'] if str(post["id"]) not in existing_id_set]

        if data:  # Only insert if there are new posts
            result = supabase.table("seen_posts").insert(data).execute()
            return result.data
        return []
    except Exception as e:
        print(f"Error saving posts: {str(e)}")
        return None

def get_seen_posts(since_timestamp=None, max_results=100):
    """
    Get posts from the seen_posts table, optionally filtered by timestamp
    
    Args:
        since_timestamp (str, optional): Only return posts after this timestamp
        max_results (int, optional): Maximum number of results to return (default 100)
        
    Returns:
        list: Array of post objects from the seen_posts table
    """
    response = refresh_or_get_supabase_client()
    
    try:
        query = supabase.table("seen_posts").select("*")
        
        if since_timestamp:
            query = query.gte("timestamp", since_timestamp)
            
        query = query.limit(max_results)
            
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error getting seen posts: {str(e)}")
        return None

def update_nft_processed_status(network, contract_address, token_id, status = "true"):
    """
    Update the processed_status for a given NFT in the nft_discovery table
    
    Args:
        network (str): The blockchain network (e.g. 'ethereum', 'polygon')
        contract_address (str): The NFT contract address
        token_id (str): The token ID of the NFT
        status (str): The status to set (default is "true")
    Returns:
        dict: Response from Supabase update operation
    """
    print(f"Updating NFT processed status for {network}:{contract_address}:{token_id} to {status}")
    response = refresh_or_get_supabase_client()
    
    try:        
        result = supabase.table("nft_discovery") \
            .update({"processed_status": status}) \
            .eq("network", network) \
            .eq("contract_address", contract_address) \
            .eq("token_id", token_id) \
            .execute()
            
        return result.data
    except Exception as e:
        print(f"Error updating NFT processed status: {str(e)}")
        return None

def count_nfts_by_contract(contract_address):
    """
    Count how many NFTs exist in nft_discovery table for a given contract address
    
    Args:
        contract_address (str): The NFT contract address to check
        
    Returns:
        int: Number of NFTs found for the contract address, or 0 if error occurs
    """
    response = refresh_or_get_supabase_client()
    
    try:
        result = supabase.table("nft_discovery") \
            .select("*", count="exact") \
            .eq("contract_address", contract_address) \
            .execute()
            
        return result.count
    except Exception as e:
        print(f"Error counting NFTs for contract {contract_address}: {str(e)}")
        return 0


def check_nft_exists(network, contract_address, token_id):
    """
    Check if an NFT already exists in the nft_discovery table
    
    Args:
        network (str): The blockchain network (e.g. 'ethereum', 'polygon')
        contract_address (str): The NFT contract address
        token_id (str): The token ID of the NFT
        
    Returns:
        bool: True if NFT exists, False otherwise
    """
    response = refresh_or_get_supabase_client()

    id = hashlib.sha256(f"{network}:{contract_address}:{token_id}:{str(datetime.now())}".encode()).hexdigest()
    
    try:
        result = supabase.table("nft_discovery") \
            .select("*") \
            .eq("id", id) \
            .execute()
            
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking NFT existence: {str(e)}")
        return False

def get_unprocessed_nfts(max_amount=10):
    """
    Get unprocessed NFTs from the nft_discovery table
    
    Args:
        max_amount (int): Maximum number of NFTs to return
        
    Returns:
        list: List of unprocessed NFT records
    """
    response = refresh_or_get_supabase_client()
    
    try:
        result = supabase.table("nft_discovery") \
            .select("*") \
            .eq("processed_status", "false") \
            .order("timestamp", desc=True) \
            .limit(max_amount) \
            .execute()
            
        return result.data
    except Exception as e:
        print(f"Error getting unprocessed NFTs: {str(e)}")
        return []

def get_latest_memory():
    """
    Get the latest memory object from the memory table, sorted by timestamp
    
    Returns:
        dict: The latest memory object or None if no memories exist
    """
    response = refresh_or_get_supabase_client()
    
    try:
        result = supabase.table("memory") \
            .select("memory_object") \
            .order("timestamp", desc=True) \
            .limit(1) \
            .execute()
            
        if result.data:
            return result.data[0]["memory_object"]
        return None
    except Exception as e:
        print(f"Error getting latest memory: {str(e)}")
        return "None"

def insert_memory(memory_object):
    """
    Insert a new memory object with current timestamp
    
    Args:
        memory_object (dict): The memory object to insert
        
    Returns:
        bool: True if successful, False otherwise
    """
    response = refresh_or_get_supabase_client()
    
    try:
        result = supabase.table("memory") \
            .insert({
                "id": hashlib.sha256(f"{str(datetime.now())}".encode()).hexdigest(),
                "memory_object": memory_object,
                "timestamp": str(datetime.now())
            }) \
            .execute()
            
        return True
    except Exception as e:
        print(f"Error inserting memory: {str(e)}")
        return False


def main():
    supabase = get_supabase_client()
    from datetime import timezone
    print("Successfully connected to Supabase!")

    # time_now_utc = datetime.now(timezone.utc)
    # time_now_utc_iso = time_now_utc.isoformat()
    # nft_batch = get_nft_batch_post(since_timestamp=time_now_utc_iso)
    # print(nft_batch)

    print(get_unique_nfts_count("0x80792de793799c57ee5febf97617393bfd7bae71"))

    # print(get_all_posts_replied_to())

if __name__ == "__main__":
    main()


