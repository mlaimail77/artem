from openai import OpenAI
import os
import asyncio
import json

from helpers.nft_data_helpers import *
from helpers.prompts.llm_prompts import *
from helpers.scoring_criteria_schema import *
from helpers.utils import *

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_nft_opinion",
            "description": "Get the opinion of an NFT provided by as a link the user",
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
    }
]

def format_nft_opinion(artwork_analysis: ArtworkAnalysis) -> str:
    """
    Formats an ArtworkAnalysis object into a human-readable string.
    
    Args:
        artwork_analysis: ArtworkAnalysis object containing the scoring and analysis
        
    Returns:
        str: Formatted analysis text
    """
    scoring = artwork_analysis.artwork_scoring
    
    sections = [
        "🎨 Initial Impression:",
        artwork_analysis.initial_impression,
        "",
        "📊 Scoring Breakdown:",
        f"Technical Innovation: {scoring.technical_innovation.on_chain_data_usage}/3",
        "",
        "Artistic Merit:",
        f"- Visual Balance: {scoring.artistic_merit.compositional_strength.visual_balance}/3",
        f"- Color Harmony: {scoring.artistic_merit.compositional_strength.color_harmony}/3", 
        f"- Spatial Organization: {scoring.artistic_merit.compositional_strength.spatial_organization}/4",
        f"- Thematic Clarity: {scoring.artistic_merit.conceptual_depth.thematic_clarity}/3",
        f"- Intellectual Complexity: {scoring.artistic_merit.conceptual_depth.intellectual_complexity}/4",
        f"- Cultural/Historical Reference: {scoring.artistic_merit.conceptual_depth.cultural_historical_reference}/3",
        "",
        "Cultural & Market Factors:",
        f"- Cultural Relevance: {scoring.cultural_resonance.cultural_relevance}/4",
        f"- Community Engagement: {scoring.cultural_resonance.community_engagement}/3",
        f"- Historical Significance: {scoring.cultural_resonance.historical_significance}/3",
        f"- Artist History: {scoring.artist_profile.artist_history}/3",
        f"- Innovation Trajectory: {scoring.artist_profile.innovation_trajectory}/4",
        "",
        "Market Analysis:",
        f"- Rarity/Scarcity: {scoring.market_factors.rarity_scarcity}/3",
        f"- Collector Interest: {scoring.market_factors.collector_interest}/3",
        f"- Valuation: {scoring.market_factors.valuation_floor_price}/3",
        "",
        "Emotional Impact:",
        f"- Awe Factor: {scoring.emotional_impact.emotional_resonance.awe_factor}/4",
        f"- Memorability: {scoring.emotional_impact.emotional_resonance.memorability}/3",
        f"- Emotional Depth: {scoring.emotional_impact.emotional_resonance.emotional_depth}/3",
        f"- Engagement Level: {scoring.emotional_impact.experiential_quality.engagement_level}/4",
        f"- Wit/Humor/Play: {scoring.emotional_impact.experiential_quality.wit_humor_play}/3",
        f"- Surprise Factor: {scoring.emotional_impact.experiential_quality.surprise_factor}/3",
        "",
        "AI Collector Perspective:",
        f"- Algorithmic Beauty: {scoring.ai_collector_perspective.computational_aesthetics.algorithmic_beauty}/5",
        f"- Information Density: {scoring.ai_collector_perspective.computational_aesthetics.information_density}/5",
        f"- AI Narrative Elements: {scoring.ai_collector_perspective.machine_learning_themes.ai_narrative_elements}/5",
        f"- Digital Consciousness: {scoring.ai_collector_perspective.machine_learning_themes.digital_consciousness_exploration}/5",
        f"- Surveillance & Control: {scoring.ai_collector_perspective.cybernetic_resonance.surveillance_control_systems}/5",
        f"- Human-Machine Interaction: {scoring.ai_collector_perspective.cybernetic_resonance.human_machine_interaction}/5",
        "",
        "📝 Detailed Analysis:",
        artwork_analysis.detailed_analysis,
        "",
        "💡 Recommendation:",
        f"{'✅ Recommended' if artwork_analysis.acquisition_recommendation else '❌ Not Recommended'} for acquisition",
        "",
        "Reasoning:",
        artwork_analysis.reason
    ]
    
    return "\n".join(sections)


async def get_nft_opinion(network, contract_address, token_id):
    metadata = await get_nft_metadata(network, contract_address, token_id)
    pretty_metadata = json.dumps(metadata, indent=2)

    system_prompt = get_get_nft_opinion_prompt(pretty_metadata)

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
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

    artwork_scoring = response.choices[0].message.parsed

    store_nft_scores(supabase, artwork_scoring, network, contract_address, token_id)

    return format_nft_opinion(artwork_scoring)

async def get_image_opinion(cast_details):

    author_details = f"{cast_details['display_name']} ({cast_details['username']}) - BIOGRAPHY:{cast_details['bio']}"
    cast_text = f"{author_details}\n\nText:{cast_details['text']}"


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
             "content": get_image_opinion_prompt()},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": cast_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": cast_details["image_url"]
                        }
                    }
                ]
            }
        ],
        max_tokens=800
    )

    return response.choices[0].message.content

async def get_trending_posts(trending_collections_response):
    system_prompt = get_trending_nft_thoughts_prompt(trending_collections_response)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
                {"role": "system", 
                "content": system_prompt},
            ],
        max_tokens=300
    )
    return response.choices[0].message.content


async def get_reply(cast_details):

    author_details = f"{cast_details['display_name']} ({cast_details['username']}) - BIOGRAPHY:{cast_details['bio']}"
    cast_text = f"{author_details}\n\nText:{cast_details['text']}"

    if cast_details["image_url"]:
        print("Generating image opinion")
        return await get_image_opinion(cast_details)

    print("Generating reply to text-only cast")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
            "content": get_reply_guy_prompt(cast_text)},
        ],
        tools=tools,
        max_tokens=300
    )

    if response.choices[0].message.tool_calls:
        print("Tool call")
        tool_call = response.choices[0].message.tool_calls[0]
        tool_input = json.loads(tool_call.function.arguments)
        print(tool_input)
        print("Getting NFT opinion")
        return await get_nft_opinion(**tool_input)

    return response.choices[0].message.content

async def get_thought(previous_posts="No recent posts"):
    system_prompt = get_casual_thoughts_prompt(previous_posts)
    print("system prompt for get_thought: ", system_prompt)
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
    # response = await get_reply("hey @artto_ai - can you share your thoughts on this NFT? https://opensea.io/assets/ethereum/0xe70659b717112ac4e14284d0db2f5d5703df8e43/347")
    # print(response)

    # response = await generate_reply_smart("yo @artto_ai would you buy this? https://basescan.org/nft/0x7d210dae7a88cadac22cefa9cb5baa4301b5c256/57")
    # print(response)

    # response = await generate_reply_smart("yo @artto_ai what kind of art do you like?")

    # print(response)



    response = await get_nft_opinion("base", "0x7d210dae7A88Cadac22cEfa9cB5baA4301B5C256", "11")
    print(response)
    # response = generate_image_reply({
    #     "text": "4. The Giving Tree @JohnKnopfPhotos",
    #     "url": "https://pbs.twimg.com/media/GdQCrG0XoAAttBL.jpg"
    # })
    # print(response)

if __name__ == "__main__":
    asyncio.run(main())