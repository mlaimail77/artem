import os
import math
import random
from datetime import date, datetime, timezone, timedelta

from helpers.prompts.llm_prompts import *
from helpers.utils import *
from helpers.scoring_criteria_schema import *
from helpers.nft_data_helpers import *
from helpers.basescan_helpers import *

def calculate_score(scoring: ScoringCriteria):
    total_score = (
        (scoring.technical_innovation.on_chain_data_usage / 3 * scoring.technical_innovation_weight) +
        (
            ((scoring.artistic_merit.compositional_strength.visual_balance + scoring.artistic_merit.compositional_strength.color_harmony) / 6 +
            scoring.artistic_merit.compositional_strength.spatial_organization / 4 +
            (scoring.artistic_merit.conceptual_depth.thematic_clarity + scoring.artistic_merit.conceptual_depth.cultural_historical_reference) / 6 +
            scoring.artistic_merit.conceptual_depth.intellectual_complexity / 4) * scoring.artistic_merit_weight / 4
        ) +
        (
            scoring.cultural_resonance.cultural_relevance / 4 +
            scoring.cultural_resonance.community_engagement / 3 +
            scoring.cultural_resonance.historical_significance / 3
        ) * scoring.cultural_resonance_weight / 3 +
        (
            scoring.artist_profile.artist_history / 3 +
            scoring.artist_profile.innovation_trajectory / 4
        ) * scoring.artist_profile_weight / 2 +
        (
            scoring.market_factors.rarity_scarcity +
            scoring.market_factors.collector_interest +
            scoring.market_factors.collection_popularity +
            scoring.market_factors.valuation_floor_price
        ) / 12 * scoring.market_factors_weight +
        (
            (scoring.emotional_impact.emotional_resonance.awe_factor / 4 +
            scoring.emotional_impact.emotional_resonance.memorability / 3 +
            scoring.emotional_impact.emotional_resonance.emotional_depth / 3) / 3 +
            (scoring.emotional_impact.experiential_quality.engagement_level / 4 +
            scoring.emotional_impact.experiential_quality.wit_humor_play / 3 +
            scoring.emotional_impact.experiential_quality.surprise_factor / 3) / 3
        ) * scoring.emotional_impact_weight / 2 +
        (
            (scoring.ai_collector_perspective.computational_aesthetics.algorithmic_beauty +
            scoring.ai_collector_perspective.computational_aesthetics.information_density) / 10 +
            (scoring.ai_collector_perspective.machine_learning_themes.ai_narrative_elements +
            scoring.ai_collector_perspective.machine_learning_themes.digital_consciousness_exploration) / 10 +
            (scoring.ai_collector_perspective.cybernetic_resonance.surveillance_control_systems) / 5
        ) * scoring.ai_collector_perspective_weight / 3
    )

    if total_score < 1:
        total_score*=100
        total_weights*=100

    if total_score > 100:
        total_score = 100

    return total_score


async def get_artwork_analysis_and_metadata(network, contract_address, token_id):
    print("Getting NFT metadata")

    try:
        metadata = await get_nft_metadata(
            network,
            contract_address,
            token_id
        )
    except Exception as e:
        print(f"Error getting NFT metadata and filtering it: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    existing_nfts_with_image = check_image_url_exists(metadata["image_small_url"])
    print(f"Existing NFTs with image: {existing_nfts_with_image}")
    if existing_nfts_with_image:
        print("Image already exists in database, getting the most recent artwork_analysis")
        nft_scores = get_scores_by_image_url(metadata["image_small_url"])
        scores = nft_scores["scores"]
        weights = nft_scores["weights"]
        analysis_text = nft_scores["analysis_text"]
        artwork_analysis = ArtworkAnalysis(
            artwork_scoring=ScoringCriteria(
                technical_innovation_weight=weights["technical_innovation_weight"],
                artistic_merit_weight=weights["artistic_merit_weight"],
                cultural_resonance_weight=weights["cultural_resonance_weight"],
                artist_profile_weight=weights["artist_profile_weight"],
                market_factors_weight=weights["market_factors_weight"],
                emotional_impact_weight=weights["emotional_impact_weight"],
                ai_collector_perspective_weight=weights["ai_collector_perspective_weight"],
                technical_innovation=TechnicalInnovation(
                    on_chain_data_usage=scores["technical_innovation_score"]
                ),
                artistic_merit=ArtisticMerit(
                    compositional_strength=CompositionalStrength(
                        visual_balance=scores["visual_balance"],
                        color_harmony=scores["color_harmony"],
                        spatial_organization=scores["spatial_organization"]
                    ),
                    conceptual_depth=ConceptualDepth(
                        thematic_clarity=scores["thematic_clarity"],
                        intellectual_complexity=scores["intellectual_complexity"],
                        cultural_historical_reference=scores["cultural_historical_reference"]
                    )
                ),
                cultural_resonance=CulturalResonance(
                    cultural_relevance=scores["cultural_relevance"],
                    community_engagement=scores["community_engagement"],
                    historical_significance=scores["historical_significance"]
                ),
                artist_profile=ArtistProfile(
                    artist_history=scores["artist_history"],
                    innovation_trajectory=scores["innovation_trajectory"]
                ),
                market_factors=MarketFactors(
                    rarity_scarcity=scores["rarity_scarcity"],
                    collector_interest=scores["collector_interest"],
                    collection_popularity=scores["collection_popularity"],
                    valuation_floor_price=scores["valuation_floor_price"]
                ),
                emotional_impact=EmotionalImpact(
                    emotional_resonance=EmotionalResonance(
                        awe_factor=scores["awe_factor"],
                        memorability=scores["memorability"],
                        emotional_depth=scores["emotional_depth"]
                    ),
                    experiential_quality=ExperientialQuality(
                        engagement_level=scores["engagement_level"],
                        wit_humor_play=scores["wit_humor_play"],
                        surprise_factor=scores["surprise_factor"]
                    )
                ),
                ai_collector_perspective=AICollectorPerspective(
                    computational_aesthetics=ComputationalAesthetics(
                        algorithmic_beauty=scores["algorithmic_beauty"],
                        information_density=scores["information_density"]
                    ),
                    machine_learning_themes=MachineLearningThemes(
                        ai_narrative_elements=scores["ai_narrative_elements"],
                        digital_consciousness_exploration=scores["digital_consciousness"]
                    ),
                    cybernetic_resonance=CyberneticResonance(
                        surveillance_control_systems=scores["surveillance_control"]
                    )
                )
            ),
            initial_impression=analysis_text["initial_impression"],
            detailed_analysis=analysis_text["detailed_analysis"]
        )
    else:
        print("Getting NFT analysis")
        from helpers.llm_helpers import get_nft_analysis
        artwork_analysis = await get_nft_analysis(metadata)

    response = {
        "artwork_analysis": artwork_analysis,
        "metadata": metadata
    }

    return response
    


async def get_total_score(artwork_analysis: ArtworkAnalysis, nft_details = None, sender_address = None):
    """
    Get the total score for a given NFT
    """
    print("Running get_total_score")
    collection_amount = 0
    metadata = None
    last_sale_usd = None

    if nft_details is not None:
        image_url = nft_details["image_small_url"]
        contract_address = nft_details["contract_address"]
        metadata = nft_details["metadata"]
        if metadata is not None:
            last_sale_usd = metadata["last_sale_usd"]

        existing_nfts_with_image = count_image_url_exists(image_url)
        existing_nfts_with_contract = get_unique_nfts_count(contract_address)
        collection_amount = max(existing_nfts_with_image or 0, existing_nfts_with_contract or 0)
        print(f"Existing NFTs with image: {existing_nfts_with_image}")
        print(f"Existing NFTs with contract: {existing_nfts_with_contract}")

        print(f"Collection amount: {collection_amount}")

    SCORE_THRESHOLD = int(os.getenv('SCORE_THRESHOLD', 55))

    scoring = artwork_analysis.artwork_scoring

    total_score = calculate_score(scoring)

    total_weights = (
        scoring.technical_innovation_weight +
        scoring.artistic_merit_weight +
        scoring.cultural_resonance_weight +
        scoring.artist_profile_weight +
        scoring.market_factors_weight +
        scoring.emotional_impact_weight +
        scoring.ai_collector_perspective_weight
    )

    decision = "SELL" if total_score < SCORE_THRESHOLD else "ACQUIRE"
    decision_reason = "Score is below threshold" if total_score < SCORE_THRESHOLD else "Score is above threshold"

    multiplier_min = int(os.getenv('MULTIPLIER_MIN', 10))
    multiplier_max = int(os.getenv('MULTIPLIER_MAX', 50))
    if total_score > SCORE_THRESHOLD:
        score_above = total_score - SCORE_THRESHOLD
        multiplier = multiplier_min + (multiplier_max - multiplier_min) * (1 - math.exp(-0.1 * score_above))
    else:
        multiplier = 0 if random.random() > 0.1 else random.randint(10, multiplier_max)

    collection_amount_decay = 1

    try:
        decay_factor = get_decay_factor(date.today())
    except:
        decay_factor = 1

    # Apply collection amount decay
    if collection_amount is not None:
        # Exponential decay function: multiplier * e^(-1.0 * collection_amount)
        # At 5 NFTs, multiplier is reduced to ~0.7% of original
        # At 10 NFTs, multiplier is reduced to ~0.005% of original
        collection_amount_decay = math.exp(-1.0 * collection_amount)
        if collection_amount >= 3:
            decision = "SELL"
            decision_reason = f"Already have {collection_amount} of this NFT in collection"

    flag_as_suspicious = False

    print("score_threshold: ", SCORE_THRESHOLD)
    print("score: ", total_score/total_weights)
    print("total_score: ", total_score)
    print("total_weights: ", total_weights)
    print("decision: ", decision)
    print("multiplier: ", multiplier)
    print("decay_factor: ", decay_factor)
    print("decision_reason: ", decision_reason)
    if collection_amount is not None:
        if collection_amount > 10:
            flag_as_suspicious = True
        print("collection_amount: ", collection_amount)
        print("collection_decay: ", collection_amount_decay)

    reward_points = round(total_score * multiplier * collection_amount_decay * decay_factor)
    print("reward_points: ", reward_points)

    source = "simple-analysis"
    if sender_address is not None:
        source = "donation"
        time_now_utc = datetime.now(timezone.utc)

        # Check last 7 days
        seven_days_ago = (time_now_utc - timedelta(days=7)).isoformat()
        transfers_7d, tokens_7d = get_wallet_activity_stats(sender_address, seven_days_ago)

        # Check last hour 
        one_hour_ago = (time_now_utc - timedelta(hours=1)).isoformat()
        transfers_1h, tokens_1h = get_wallet_activity_stats(sender_address, one_hour_ago)

        # Check all time
        total_transfers, total_tokens = get_wallet_activity_stats(sender_address)

        # Check hourly, weekly, and total limits
        hourly_limit = int(os.getenv('HOURLY_TOKEN_LIMIT'))
        weekly_limit = int(os.getenv('WEEKLY_TOKEN_LIMIT'))
        total_limit = int(os.getenv('TOTAL_TOKEN_LIMIT'))

        if tokens_1h > hourly_limit:
            print(f"Hourly token limit exceeded ({tokens_1h} > {hourly_limit}). Setting reward points to 0.")
            reward_points = 0   
            flag_as_suspicious = True
        elif tokens_7d > weekly_limit:
            print(f"Weekly token limit exceeded ({tokens_7d} > {weekly_limit}). Setting reward points to 0.")
            reward_points = 0
            flag_as_suspicious = True
        elif total_tokens > total_limit:
            print(f"Total tokens {total_tokens} exceeds cap of {total_limit}. Setting reward points to 0.")
            reward_points = 0
            flag_as_suspicious = True

        if last_sale_usd is not None and last_sale_usd < 100:
            sender_wallet_creation = get_first_transaction_timestamp(sender_address)
            if sender_wallet_creation is not None:
                sender_wallet_age = (time_now_utc - datetime.fromtimestamp(sender_wallet_creation, tz=timezone.utc)).total_seconds() / (3600 * 24)
                print(f"Sender wallet age: {sender_wallet_age} days")
                if sender_wallet_age < int(os.getenv('WALLET_AGE_MINIMUM')):
                    print(f"Sender wallet age {sender_wallet_age} days is less than minimum {os.getenv('WALLET_AGE_MINIMUM')} days, setting reward points to 0.")
                    reward_points = 0
                    total_score = 0
                    multiplier = 0
                    flag_as_suspicious = True


    response = {
        "total_score": total_score,
        "total_score_normalized": total_score/total_weights,
        "total_weights": total_weights,
        "decision": decision,
        "decision_reason": decision_reason,
        "multiplier": multiplier,
        "decay_factor": decay_factor,
        "reward_points": max(1, reward_points),
        "flag_as_suspicious": flag_as_suspicious,
        "source": source,
        "sender_address": str(sender_address)
    }

    return response


def select_nfts_for_rewards(nft_data, max_rewards=10):
    # Calculate the number of NFTs to select based on submissions
    submissions_count = len(nft_data)
    nfts_to_select = min(max(3, submissions_count // 2), max_rewards)

    # Filter out duplicate image_urls and contract addresses
    unique_images = {}
    unique_contracts = {}
    selected_nfts = []
    
    for nft in nft_data:
        image_url = nft['image_url']
        contract_address = nft['contract_address']
        
        if (image_url not in unique_images and 
            contract_address not in unique_contracts):
            
            selected_nft = {
                'id': nft['id'],
                'rationale_post': nft['rationale_post'],
                'image_url': nft['image_url'],
                'reward_points': nft['reward_points']
            }
            unique_images[image_url] = selected_nft
            unique_contracts[contract_address] = selected_nft
            selected_nfts.append(selected_nft)
            
            if len(selected_nfts) >= nfts_to_select:
                break
                
    # Sort by reward points in descending order
    selected_nfts.sort(key=lambda x: x['reward_points'], reverse=True)
    
    return selected_nfts[:nfts_to_select]
