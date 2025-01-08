from helpers.opensea_helpers import *
from helpers.utils import *
from helpers.nft_data_helpers import *
from helpers.opensea_helpers import *

from dotenv import load_dotenv

load_dotenv('.env.local')

def get_top_quartile(nft_batch):
    scored_nfts = []
    for nft in nft_batch:
        if 'total_score' in nft:
            scored_nfts.append(nft)
            
    if scored_nfts:
        scored_nfts.sort(key=lambda x: x['total_score'], reverse=True)
        quartile_size = max(1, len(scored_nfts) // 4)
        return scored_nfts[:quartile_size]
    else:
        return []

async def get_nft_batch_for_sale(last_n_days=None, max_amount=20):

    if last_n_days is not None:
        time_now_utc = datetime.now(timezone.utc)
        n_days_ago = time_now_utc - timedelta(days=last_n_days)
        n_days_ago_utc_iso = n_days_ago.isoformat()
        print(n_days_ago_utc_iso)
        nft_batch = get_nfts_to_sell(
            since_timestamp=n_days_ago_utc_iso,
            max_amount=max_amount
        )
    else:
        nft_batch = get_nfts_to_sell(
            max_amount=max_amount
        )
    
    # Add OpenSea URL for each NFT in batch
    for nft in nft_batch:
        nft['opensea_url'] = f"https://opensea.io/assets/{nft.get('network')}/{nft.get('contract_address')}/{nft.get('token_id')}"

    # Create list of NFT IDs in required format
    nft_ids = []
    for nft in nft_batch:
        nft_id = f"{nft['network']}.{nft['contract_address']}.{nft['token_id']}"
        nft_ids.append(nft_id)

    # Get NFT details from SimpleHash API
    nft_details = get_nfts_by_token_list(nft_ids)

    # Process floor prices for each NFT
    for nft in nft_details['nfts']:
        floor_prices = nft['collection'].get('floor_prices', [])
        
        if not floor_prices:
            # No floor price available 
            floor_price = None
        elif len(floor_prices) == 1:
            # Only one floor price - use it
            floor_price = floor_prices[0]['value']
            floor_price = floor_price / 1e18 if floor_price > 0 else 0
        else:
            # Multiple floor prices - take lowest value
            floor_price = min(fp['value'] for fp in floor_prices)
            floor_price = floor_price / 1e18 if floor_price > 0 else 0
            
        # Find matching NFT in batch and add floor price
        for batch_nft in nft_batch:
            if (batch_nft['network'] == nft['chain'] and
                batch_nft['contract_address'].lower() == nft['contract_address'].lower() and 
                batch_nft['token_id'] == nft['token_id']):
                batch_nft['floor_price'] = floor_price
                break
    
    return nft_batch

async def sell_batch_process(nft_batch):

    # Split NFTs into those with and without floor prices
    nfts_with_floor = []
    nfts_without_floor = []
    
    for nft in nft_batch:
        if nft.get('floor_price') is not None and nft.get('floor_price') > 0:
            nfts_with_floor.append(nft)
        else:
            nfts_without_floor.append(nft)
            
    print(f"NFTs with floor price: {len(nfts_with_floor)}")
    print(f"NFTs without floor price: {len(nfts_without_floor)}")
    
    nfts_with_floor_ids = []
    for nft in nfts_with_floor:
        try:
            response = make_opensea_listing(
                chain=nft['network'],
                token_address=nft['contract_address'],
                token_id=nft['token_id'],
                amount=nft['floor_price'],
                bearer_token=os.getenv('OPENSEA_ARTTO_SERVER_BEARER_TOKEN'),
                endpoint="http://localhost:3001/sell-nft"
            )
            print(response)
            nfts_with_floor_ids.append(nft['id'])
        except Exception as e:
            print(f"Failed to list NFT {nft['network']}.{nft['contract_address']}.{nft['token_id']}: {str(e)}")
            continue
        
    update_nft_scores_status(nfts_with_floor_ids, "LISTED")

    if len(nfts_without_floor) > 0:
        nfts_without_floor_ids = []
        for nft in nfts_without_floor:
            try:
                response = make_opensea_auction(
                    chain=nft['network'],
                    token_address=nft['contract_address'],
                    token_id=nft['token_id'],
                    amount=0.0001,
                    bearer_token=os.getenv('OPENSEA_ARTTO_SERVER_BEARER_TOKEN'),
                    endpoint="http://localhost:3001/sell-nft"
                )
                print(response)
                nfts_without_floor_ids.append(nft['id'])
            except Exception as e:
                print(f"Failed to auction NFT {nft['network']}.{nft['contract_address']}.{nft['token_id']}: {str(e)}")
                try:
                    response = make_opensea_listing(
                        chain=nft['network'],
                        token_address=nft['contract_address'],
                        token_id=nft['token_id'],
                        amount=0.01,
                        bearer_token=os.getenv('OPENSEA_ARTTO_SERVER_BEARER_TOKEN'),
                        endpoint="http://localhost:3001/sell-nft"
                    )
                    print(response)
                except Exception as e:
                    print(f"Failed to list NFT {nft['network']}.{nft['contract_address']}.{nft['token_id']}: {str(e)}")
                    continue
                continue
            
        update_nft_scores_status(nfts_without_floor_ids, "AUCTIONED")

    # Merge both batches and add listing type
    processed_batch = []
    
    for nft in nfts_with_floor:
        nft['listing_type'] = 'LISTED'
        processed_batch.append(nft)
        
    for nft in nfts_without_floor:
        nft['listing_type'] = 'AUCTIONED' 
        processed_batch.append(nft)
    
    return processed_batch