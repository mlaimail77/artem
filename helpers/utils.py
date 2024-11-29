import os
import json
from datetime import datetime
from supabase import create_client, Client

from dotenv import load_dotenv # can be installed with `pip install python-dotenv`

load_dotenv('.env.local')

def get_supabase_client():
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    supabase.auth.sign_in_with_password({ "email": os.getenv("SUPABASE_USER"), "password": os.getenv("SUPABASE_PASSWORD") })
    return supabase

def get_last_n_posts(supabase, n=10):
    response = supabase.auth.refresh_session()

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

def get_all_posts_replied_to(supabase):
    response = supabase.auth.refresh_session()
    response = supabase.table("posts_created").select("parent_id").execute()
    return response.data


def get_all_posts(supabase):
    response = supabase.table("posts_created").select("*").execute()
    return response.data

def store_nft_scores(supabase, artwork_scoring, network, contract_address, token_id):
    """
    Store artwork scoring and metadata in Supabase database
    
    Args:
        supabase: Supabase client instance
        artwork_scoring: ScoringCriteria object containing artwork analysis
        network: Blockchain network (e.g. 'ethereum')
        contract_address: NFT contract address
        token_id: NFT token ID
        
    Returns:
        dict: Response data from Supabase insert
    """
    response = supabase.auth.refresh_session()

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
        "human_machine_interaction": artwork_scoring.ai_collector_perspective.cybernetic_resonance.human_machine_interaction,        
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
        "initial_impression": artwork_scoring.initial_impression,
        "detailed_analysis": artwork_scoring.detailed_analysis,
        "acquisition_recommendation": artwork_scoring.acquisition_recommendation,
        "reason": artwork_scoring.reason
    }

    response = supabase.table("nft_scores").insert(
        {
            "id": f"{network}:{contract_address}:{token_id}",
            "network": network,
            "contract_address": contract_address, 
            "token_id": token_id,
            "timestamp": str(datetime.now()),
            "scores": json.dumps(scores),
            "weights": json.dumps(weights),
            "analysis_text": json.dumps(analysis_text)
        }
    ).execute()
    return response.data


def set_post_created(supabase, post):
    response = supabase.auth.refresh_session()
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

supabase = get_supabase_client()
print("Successfully connected to Supabase!")

def main():
    supabase = get_supabase_client()
    print("Successfully connected to Supabase!")

    # print(user)

    # response = (
    #     supabase.table("countries")
    #     .insert({"id": 1, "name": "Denmark"})
    #     .execute()
    # )    
    # print(response.content)

    # sample_post = {
    #     'hash': '0x123abc123xyz',
    #     'text': 'This is a sample post',
    #     'parent_id': '0x000FFF'
    # }
    # set_post_created(supabase, sample_post)
    # get_posts(supabase)


if __name__ == "__main__":
    main()


