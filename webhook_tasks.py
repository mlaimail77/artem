from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.farcaster_helpers import *

import logging

logger = logging.getLogger(__name__)

async def process_webhook(webhook_data):
    try:
        # Map network from webhook to SimpleHash API format
        if webhook_data['network'] == 'base-mainnet':
            network = 'base'
        elif webhook_data['network'] == 'base-sepolia':
            network = 'base-sepolia'
        else:
            network = webhook_data['network']

        token_id = webhook_data['tokenId']
        from_address = webhook_data['from']
        contract_address = webhook_data['contractAddress']

        post_content = f"I just received token #{token_id} from {from_address}!"
        print(post_content)

        metadata = await get_nft_metadata(network, contract_address, token_id)
        artwork_analysis = await get_nft_analysis(metadata)
        final_decision = await get_final_decision(artwork_analysis)

        decision = final_decision.decision
        rationale_post = final_decision.rationale_post

        if decision == "BURN":
            print("BURN THAT SHIT!")
            post_long_cast(rationale_post)
            # transfer(
            #     wallet=wallet,
            #     amount=1,
            #     asset_id=contract_address,
            #     destination="BURN_ADDRESS"
            # )
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
    reply = await get_reply(cast_details)
    react_cast('like', cast["hash"])
    print(reply)
    response = post_long_cast(reply, parent=cast["hash"])
