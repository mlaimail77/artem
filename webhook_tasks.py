from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.farcaster_helpers import *
from helpers.coinbase_helpers import *

import logging

logger = logging.getLogger(__name__)

async def process_webhook(webhook_data):
    try:
        # Skip if not a transaction event
        if webhook_data.get('eventType') == 'transaction':
            logger.info(f"Skipping - event type is transaction")
            return {
                'status': 'skipped', 
                'reason': 'Transaction event'
            }

        # Only process if this is an incoming transfer to our wallet
        if webhook_data['to'].lower() not in [os.getenv('ARTTO_ADDRESS_SEPOLIA').lower(), os.getenv('ARTTO_ADDRESS_MAINNET').lower()]:
            logger.info(f"Skipping - transfer not to our wallet address")
            return {
                'status': 'skipped',
                'reason': 'Not incoming transfer'
            }
        
        # Map network from webhook to SimpleHash API format
        if webhook_data['network'] == 'base-mainnet':
            network = 'base'
            current_wallet_address = os.getenv('ARTTO_ADDRESS_MAINNET')
            wallet = wallet_mainnet
        elif webhook_data['network'] == 'base-sepolia':
            network = 'base-sepolia'
            current_wallet_address = os.getenv('ARTTO_ADDRESS_SEPOLIA')
            wallet = wallet_sepolia
        else:
            network = webhook_data['network']
            current_wallet_address = os.getenv('ARTTO_ADDRESS_MAINNET')

        token_id = webhook_data['tokenId']
        from_address = webhook_data['from']
        contract_address = webhook_data['contractAddress']
        post_content = f"I just received token #{token_id} from {from_address}!"
        print(post_content)

        metadata = await get_nft_metadata(network, contract_address, token_id)
        artwork_analysis = await get_nft_analysis(metadata)
        final_decision = await get_final_decision(artwork_analysis, metadata, from_address)

        decision = final_decision.decision
        rationale_post = final_decision.rationale_post
        if 'image_medium_url' in metadata:
            rationale_post += f" {metadata['image_medium_url']}"

        store_nft_scores(artwork_analysis, metadata["image_medium_url"], network, contract_address, token_id)

        if decision == "BURN":
            print("BURN THAT SHIT!")
            post_long_cast(rationale_post)
            response = transfer_nft(wallet,
                 network_id=webhook_data['network'], 
                 contract_address=contract_address, 
                 from_address=current_wallet_address, 
                 to_address="0x000000000000000000000000000000000000dEaD", 
                 token_id=token_id)
            print(response)
        else:
            post_long_cast(rationale_post)
            print("KEEP!")
            

        #TODO(should be a cast)
        print("rationale_post", rationale_post)

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
    reply, scores = await get_reply(cast_details)
    react_cast('like', cast["hash"])
    print(reply)
    response = post_long_cast(reply, parent=cast["hash"])
