import os
import json
import random
import yaml
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
        .select("*") \
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

def store_nft_scores(scores_object, score_calcs, final_decision = None):
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

    response = refresh_or_get_supabase_client()

    artwork_analysis = scores_object["artwork_analysis"]
    image_url = scores_object["image_small_url"]
    network = scores_object["chain"]
    contract_address = scores_object["contract_address"]
    token_id = scores_object["token_id"]

    artwork_scoring = artwork_analysis.artwork_scoring
    initial_impression = artwork_analysis.initial_impression
    detailed_analysis = artwork_analysis.detailed_analysis

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


    total_score = score_calcs["total_score"]

    multiplier = score_calcs["multiplier"]
    decay_factor = score_calcs["decay_factor"]
    reward_points = score_calcs["reward_points"]


    print(f"Total score: {total_score}")

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
        "multiplier": round(multiplier, 4),
        "decay_factor": round(decay_factor, 4),
        "reward_points": round(reward_points, 4)
    }

    if existing.data:
        # Update existing record
        response = supabase.table("nft_scores").update(artwork_data).eq("network", network).eq("contract_address", contract_address).eq("token_id", token_id).execute()
    else:
        # Insert new record
        artwork_data["id"] = hashlib.sha256(f"{network}:{contract_address}:{token_id}:{str(datetime.now())}".encode()).hexdigest()
        response = supabase.table("nft_scores").insert(artwork_data).execute()
    return response.data

def update_nft_scores(ids, group_posted):
    response = refresh_or_get_supabase_client()
    quoted_ids = [f'"{id}"' for id in ids]
    ids_string = f"({','.join(quoted_ids)})"

    for id in ids:
        print("id: ", id)
        response = supabase.table("nft_scores").update({"group_posted": group_posted}).eq("id", id).execute()
        print("response: ", response)
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
    response = supabase.table("nft_scores").select("id").eq("contract_address", contract_address).execute()
    
    if response.data:
        unique_ids = set(item['id'] for item in response.data)
        return len(unique_ids)
    return 0

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


