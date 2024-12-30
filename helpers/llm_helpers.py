from openai import OpenAI
import os
import asyncio
import json
import math

from helpers.nft_data_helpers import *
from helpers.prompts.llm_prompts import *
from helpers.scoring_criteria_schema import *
from helpers.spam_tweet_schema import *
from helpers.wallet_analysis import *

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_nft_opinion",
            "description": "Get the opinion of an NFT provided by as a link by the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "network": {"type": "string"},
                    "contract_address": {"type": "string"},
                    "token_id": {"type": "string"},
                },
                "required": ["network", "contract_address", "token_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function", 
        "function": {
            "name": "get_roast",
            "description": "Get a roast of a wallet address",
            "parameters": {
                "type": "object",
                "properties": {
                    "wallet_address": {"type": "string"}
                },
                "required": ["wallet_address"],
                "additionalProperties": False,
            },
        },
    }
]

def get_wallet_analysis_response(wallet_data, base64_image, tone, current_valuation):
    system_prompt, user_prompt = get_wallet_analysis_prompt(wallet_data, tone, current_valuation)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", 
             "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
    )

    return response.choices[0].message.content

def get_summary_nft_post(rationale_posts):
    system_prompt = get_summary_nft_post_prompt(rationale_posts)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}],
    )
    return response.choices[0].message.content

def get_artto_promotion(nft_collection_value, length):
    system_prompt = get_artto_promotion_prompt(nft_collection_value, length)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}],
    )
    return response.choices[0].message.content

def identify_spam(tweet):
    system_prompt = get_spam_identification_prompt(tweet)
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}],
        response_format=SpamTweet
    )
    return response.choices[0].message.parsed


def adjust_weights(weights, nft_scores):
    system_prompt = get_adjust_weights_prompt(weights, nft_scores)

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", 
             "content": system_prompt},
        ],
        response_format=UpdateWeights
    )

    new_weights = response.choices[0].message.parsed

    return new_weights

def get_total_score(artwork_analysis: ArtworkAnalysis, collection_amount = None):
    SCORE_THRESHOLD = int(os.getenv('SCORE_THRESHOLD', 55))

    scoring = artwork_analysis.artwork_scoring
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

    total_weights = (
        scoring.technical_innovation_weight +
        scoring.artistic_merit_weight +
        scoring.cultural_resonance_weight +
        scoring.artist_profile_weight +
        scoring.market_factors_weight +
        scoring.emotional_impact_weight +
        scoring.ai_collector_perspective_weight
    )

    if total_score < 1:
        total_score*=100
        total_weights*=100

    if total_score > 100:
        total_score = 100

    decision = "REJECT" if total_score < SCORE_THRESHOLD else "ACQUIRE"
    
    if total_score > SCORE_THRESHOLD + 10:
        multiplier = 200
    elif total_score > SCORE_THRESHOLD:
        multiplier = 150
    else:
        # Multiplier logic for $ARTTO rewards:
        # - Score > 45: Multiplier = 200 (max reward 20,000 $ARTTO for perfect score)
        # - Score > 35 but < 45: Multiplier = 150 (rewards between 5,250-6,750 $ARTTO)
        # - Score < 35: 90% chance of 0 multiplier, 10% chance of random 10-100 multiplier
        multiplier = 0 if random.random() > 0.1 else random.randint(10, 100)

    collection_decay = 1

    try:
        decay_factor = get_decay_factor(date.today())
    except:
        decay_factor = 1

    # Apply collection amount decay
    if collection_amount is not None:
        # Exponential decay function: multiplier * e^(-0.5 * collection_amount)
        # At 5 NFTs, multiplier is reduced to ~8% of original
        # At 10 NFTs, multiplier is reduced to ~0.7% of original
        collection_decay = math.exp(-0.5 * collection_amount)

    print("score_threshold: ", SCORE_THRESHOLD)
    print("score: ", total_score/total_weights)
    print("total_score: ", total_score)
    print("total_weights: ", total_weights)
    print("decision: ", decision)
    print("multiplier: ", multiplier)
    print("decay_factor: ", decay_factor)
    if collection_amount is not None:
        print("collection_amount: ", collection_amount)
        print("collection_decay: ", collection_decay)

    response = {
        "total_score": total_score,
        "total_score_normalized": total_score/total_weights,
        "total_weights": total_weights,
        "decision": decision,
        "multiplier": multiplier,
        "decay_factor": decay_factor,
        "reward_points": round(total_score * multiplier * collection_decay * decay_factor)
    }

    return response

async def get_nft_post(artwork_analysis: ArtworkAnalysis):
    response = get_total_score(artwork_analysis)

    decision = response["decision"]


    system_prompt = get_nft_post_prompt(artwork_analysis, decision)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt}
        ]
    )

    return response.choices[0].message.content

async def get_final_decision(nft_opinion, nft_metadata, from_address):
    response = get_total_score(nft_opinion)
    decision = response["decision"]
    reward_points = response["reward_points"]

    ens_name = get_ens_name(from_address)

    system_prompt = get_keep_or_burn_decision(nft_opinion, nft_metadata, ens_name, decision, reward_points)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
             "content": system_prompt}
        ],
        response_format=AcquireOrReject
    )

    final_decision = response.choices[0].message.parsed

    return final_decision


async def get_nft_analysis(metadata):
    pretty_metadata = json.dumps(metadata, indent=2)
    try:
        is_top_collection = await is_top_collection(metadata["collection_id"], time_period='30d')
    except:
        is_top_collection = False

    system_prompt = get_nft_analysis_prompt(pretty_metadata, is_top_collection)

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", 
             "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": metadata["image_medium_url"]
                        }
                    }
                ]
            }
        ],
        response_format=ArtworkAnalysis
    )

    artwork_analysis = response.choices[0].message.parsed

    print("artwork_analysis: ", artwork_analysis)
    return artwork_analysis

async def get_image_opinion(cast_details):

    try:
        author_details = f"{cast_details['display_name']} ({cast_details['username']}) - BIOGRAPHY:{cast_details['bio']}"
        cast_text = f"{author_details}\n\nText:{cast_details['text']}"
    except:
        cast_text = f"Text:{cast_details['text']}"


    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
             "content": get_image_analysis_prompt(cast_text)},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": cast_details["image_url"]
                        }
                    }
                ]
            }
        ],
        response_format=ArtworkAnalysisImageOnly,
    )

    image_analysis = response.choices[0].message.parsed

    print("image_analysis: ", image_analysis)

    system_prompt = get_image_analysis_post_prompt(image_analysis)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt}
        ]
    )

    return response.choices[0].message.content


async def get_thoughts_on_trending_casts(trending_casts):

    system_prompt = get_thoughts_on_trending_casts_prompt()
    messages = [
        {"role": "system", 
        "content": system_prompt},
    ]

    for cast in trending_casts:
        messages.append({
            "role": "user",
            "content": f"Post: {cast['text']} - Author: {cast['author']}"
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=500
    )
    return response.choices[0].message.content


async def get_trending_post(trending_collections_response):
    system_prompt = get_trending_nft_thoughts_prompt(trending_collections_response)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", 
                "content": system_prompt},
            ],
        max_tokens=500
    )
    return response.choices[0].message.content


async def get_reply(cast_details, post_params):

    try:
        author_details = f"{cast_details['display_name']} ({cast_details['username']}) - BIOGRAPHY:{cast_details['bio']}"
        cast_text = f"{author_details}\n\nText:{cast_details['text']}"
    except:
        cast_text = f"Text:{cast_details['text']}"

    if cast_details.get("image_url") or cast_details.get("url"):
        print("Generating image opinion")
        reply = await get_image_opinion(cast_details)
        return (reply, None)

    print("Generating reply to text-only cast")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", 
            "content": get_reply_guy_prompt(cast_text, post_params)},
        ],
        tools=tools,
        max_tokens=300
    )

    if response.choices[0].message.tool_calls:
        # Iterate through all tool calls
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "get_nft_opinion":
                print("Tool call: ", tool_call)
                tool_input = json.loads(tool_call.function.arguments)
                print("Tool input: ", tool_input)
                
                try:
                    metadata = await get_nft_metadata(**tool_input)
                    if not metadata or 'image_medium_url' not in metadata:
                        raise ValueError("NFT metadata missing required image URL")
                except Exception as e:
                    raise ValueError(f"Failed to fetch NFT metadata: {str(e)}")
                artwork_analysis = await get_nft_analysis(metadata)

                post = await get_nft_post(artwork_analysis)
                print(f"metadata: {metadata}")

                scores_object = {
                    "artwork_analysis": artwork_analysis,
                    "image_medium_url": metadata["image_medium_url"],
                    "chain": tool_input["network"],
                    "contract_address": tool_input["contract_address"],
                    "token_id": tool_input["token_id"]
                }
                return (post, scores_object)
            if tool_call.function.name == "get_roast":
                print("Tool call: ", tool_call)
                tool_input = json.loads(tool_call.function.arguments)
                print("Tool input: ", tool_input)
                wallet_data = get_wallet_info(tool_input["wallet_address"])
                current_valuation = get_wallet_valuation(tool_input["wallet_address"])

                tone_default = 3
                response = get_analysis_params(wallet_data, tone_default, current_valuation)
                os.remove(response["temp_image_path"])
                analysis = get_wallet_analysis_response(wallet_data, response["base64_image"], tone_default, current_valuation)

                return (analysis, None)

    return (response.choices[0].message.content, None)

async def get_scheduled_post(post_type, post_params, previous_posts="No recent posts", additional_context="None"):
    system_prompt = get_scheduled_post_prompt(post_type, post_params, previous_posts, additional_context)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", 
                "content": system_prompt},
            ],
        max_tokens=300
    )
    return response.choices[0].message.content


async def main():
    # pass
    
    response, scores = await get_reply("hey @artto_ai - can you share your thoughts on this NFT? https://opensea.io/assets/ethereum/0xe70659b717112ac4e14284d0db2f5d5703df8e43/347")
    print(response)

    # response = await generate_reply_smart("yo @artto_ai would you buy this? https://basescan.org/nft/0x7d210dae7a88cadac22cefa9cb5baa4301b5c256/57")
    # print(response)

    # response = await generate_reply_smart("yo @artto_ai what kind of art do you like?")

    # print(response)



    # response = await get_nft_analysis("base", "0x7d210dae7A88Cadac22cEfa9cB5baA4301B5C256", "11")
    # print(response)
    # response = generate_image_reply({
    #     "text": "4. The Giving Tree @JohnKnopfPhotos",
    #     "url": "https://pbs.twimg.com/media/GdQCrG0XoAAttBL.jpg"
    # })
    # print(response)

if __name__ == "__main__":
    asyncio.run(main())