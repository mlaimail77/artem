from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.farcaster_helpers import *
from helpers.coinbase_helpers import *
from helpers.twitter_helpers import *

import logging

logger = logging.getLogger(__name__)

async def process_webhook(webhook_data):
    try:
        # Skip if not an ADDRESS_ACTIVITY event
        if webhook_data.get('type') != 'ADDRESS_ACTIVITY':
            logger.info(f"Skipping - event type is not ADDRESS_ACTIVITY")
            return {
                'status': 'skipped',
                'reason': 'Not ADDRESS_ACTIVITY event'
            }

        activity = webhook_data['event']['activity'][0]
        to_address = activity['toAddress']

        # Only process if this is an incoming transfer to our wallet
        if to_address.lower() not in [os.getenv('ARTTO_ADDRESS_SEPOLIA').lower(), os.getenv('ARTTO_ADDRESS_MAINNET').lower()]:
            logger.info(f"Skipping - transfer not to our wallet address")
            return {
                'status': 'skipped', 
                'reason': 'Not incoming transfer'
            }

        webhook_network = webhook_data['event']['network']
        if webhook_network == 'BASE_MAINNET':
            network = 'base'
            current_wallet_address = os.getenv('ARTTO_ADDRESS_MAINNET')
            wallet = wallet_mainnet
        elif webhook_network == 'BASE_SEPOLIA':
            network = 'base-sepolia'
            current_wallet_address = os.getenv('ARTTO_ADDRESS_SEPOLIA')
            wallet = wallet_sepolia
        else:
            network = webhook_network
            current_wallet_address = os.getenv('ARTTO_ADDRESS_MAINNET')

        token_id = int(activity['erc721TokenId'], 16)  # Convert hex to decimal
        from_address = activity['fromAddress']
        contract_address = activity['rawContract']['address']
        post_content = f"I just received token #{token_id} from {from_address}!"
        print(post_content)

        print("Getting NFT metadata")
        metadata = await get_nft_metadata(network, contract_address, token_id)
        print("Getting NFT analysis")
        artwork_analysis = await get_nft_analysis(metadata)
        print("Getting final decision")
        final_decision = await get_final_decision(artwork_analysis, metadata, from_address)

        decision = final_decision.decision
        rationale_post = final_decision.rationale_post
        if 'image_medium_url' in metadata:
            rationale_post += f" {metadata['image_medium_url']}"

        scores_object = {
            "artwork_analysis": artwork_analysis,
            "image_medium_url": metadata["image_medium_url"],
            "chain": network,
            "contract_address": contract_address,
            "token_id": token_id
        }
        score_calcs = get_total_score(scores_object["artwork_analysis"])

        try:
            reward_points = score_calcs["reward_points"]
        except:
            reward_points = 0
        print("Reward points:", reward_points)
        store_nft_scores(scores_object, score_calcs)
        refreshed_token = refresh_token()

        print("Decision:", decision)
        print("Rationale:", rationale_post)

        if decision == "BURN":
            try:
                post_long_cast(rationale_post)
            except Exception as e:
                print(f"Error posting to Farcaster: {str(e)}")
            try:
                post_tweet({"text": rationale_post}, refreshed_token, parent=None)
            except Exception as e:
                print(f"Error posting to Twitter: {str(e)}")
            response = transfer_nft(wallet,
                 network_id=webhook_data['network'], 
                 contract_address=contract_address, 
                 from_address=current_wallet_address, 
                 to_address="0x000000000000000000000000000000000000dEaD", 
                 token_id=token_id)
            print(response)
        elif decision == "KEEP":
            try:
                post_long_cast(rationale_post)
            except Exception as e:
                print(f"Error posting to Farcaster: {str(e)}")
            try:
                post_tweet({"text": rationale_post}, refreshed_token, parent=None)
            except Exception as e:
                print(f"Error posting to Twitter: {str(e)}")
            print("KEEP!")
        else:
            print("UNHANDLED DECISION")

        # Transfer ARTTO tokens to the sender
        try:
            response = transfer_artto_token(
                wallet, 
                reward_points, 
                from_address
            )
            print(response)
        except Exception as e:
            print(f"Error transferring ARTTO tokens: {str(e)}")


        return {
            'status': 'success',
            'decision': decision,
            'rationale': rationale_post,
            'metadata': metadata,
            'artwork_analysis': artwork_analysis
        }

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")

        return {
            'status': 'error',
            'error': str(e)
        }

async def process_neynar_webhook(webhook_data):
    data = webhook_data      
    # Extract relevant data from webhook payload
    cast = data.get('data', {})

    cast_details = get_cast_details(cast)
    post_params = generate_post_params()
    posts_replied_to = get_all_posts_replied_to()
    if any(p['parent_id'] == cast["hash"] for p in posts_replied_to):
        print("Already replied to this parent")
        return
    reply, scores = await get_reply(cast_details, post_params)
    react_cast('like', cast["hash"])
    print(reply)
    response = post_long_cast(reply, parent=cast["hash"])
    if scores:
        score_calcs = get_total_score(scores["artwork_analysis"])
        store_nft_scores(scores, score_calcs)