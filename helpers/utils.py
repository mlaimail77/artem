import os
import json
import random
import yaml
from datetime import datetime
from supabase import create_client, Client
from helpers.prompts.casual_thought_topics import *

import hashlib

from dotenv import load_dotenv

load_dotenv('.env.local')

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
    from helpers.prompts.scoring_criteria import SCORING_CRITERIA
    return SCORING_CRITERIA

def get_taste_weights():
    return yaml.safe_load(open("helpers/prompts/taste_weights.yaml"))

def set_taste_weights(weights):
    print("setting weights")
    print(weights.updated_weights)
    print(weights.reason)
    with open("helpers/prompts/taste_weights.yaml", "w") as f:
        f.write("# NFT Evaluation Weights\n")
        f.write(f"# ({datetime.now().strftime('%Y-%m-%d')}) Update Reason: {weights.reason}\n")
        f.write(f"TECHNICAL_INNOVATION_WEIGHT: {weights.updated_weights.TECHNICAL_INNOVATION_WEIGHT}\n")
        f.write(f"ARTISTIC_MERIT_WEIGHT: {weights.updated_weights.ARTISTIC_MERIT_WEIGHT}\n") 
        f.write(f"CULTURAL_RESONANCE_WEIGHT: {weights.updated_weights.CULTURAL_RESONANCE_WEIGHT}\n")
        f.write(f"ARTIST_PROFILE_WEIGHT: {weights.updated_weights.ARTIST_PROFILE_WEIGHT}\n")
        f.write(f"MARKET_FACTORS_WEIGHT: {weights.updated_weights.MARKET_FACTORS_WEIGHT}\n")
        f.write(f"EMOTIONAL_IMPACT_WEIGHT: {weights.updated_weights.EMOTIONAL_IMPACT_WEIGHT}\n")
        f.write(f"AI_COLLECTOR_PERSPECTIVE_WEIGHT: {weights.updated_weights.AI_COLLECTOR_PERSPECTIVE_WEIGHT}\n")

def get_nft_scores(n=10):
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("id,scores,analysis_text").order("timestamp", desc=True).limit(n).execute()
    return response.data

def get_recent_nft_scores(n=6):
    response = refresh_or_get_supabase_client()
    response = supabase.table("nft_scores").select("network,contract_address,token_id,analysis_text,image_url,acquire_recommendation").order("timestamp", desc=True).limit(n).execute()
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

def get_all_posts_replied_to():
    print("Fetching posts replied to")
    response = refresh_or_get_supabase_client()
    response = supabase.table("posts_created").select("parent_id").execute()
    return response.data


def get_all_posts():
    print("Fetching all posts")
    response = refresh_or_get_supabase_client()
    response = supabase.table("posts_created").select("*").execute()
    return response.data

def store_nft_scores(scores_object, score_calcs):
    """
    Store artwork scoring and metadata in Supabase database
    
    Args:
        supabase: Supabase client instance
        scores_object: Dictionary containing artwork analysis, image URL, chain, contract address, and token ID
    Returns:
        dict: Response data from Supabase insert
    """
    response = refresh_or_get_supabase_client()

    artwork_analysis = scores_object["artwork_analysis"]
    image_url = scores_object["image_medium_url"]
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
        "acquire_recommendation": total_score > int(os.getenv('SCORE_THRESHOLD', 55))
    }

    if existing.data:
        # Update existing record
        response = supabase.table("nft_scores").update(artwork_data).eq("network", network).eq("contract_address", contract_address).eq("token_id", token_id).execute()
    else:
        # Insert new record
        artwork_data["id"] = hashlib.sha256(f"{network}:{contract_address}:{token_id}:{str(datetime.now())}".encode()).hexdigest()
        response = supabase.table("nft_scores").insert(artwork_data).execute()
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


def main():
    supabase = get_supabase_client()
    print("Successfully connected to Supabase!")

    # print(get_all_posts_replied_to())

if __name__ == "__main__":
    main()


