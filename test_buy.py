from helpers.nft_data_helpers import *
import json
from datetime import datetime, timedelta

async def test_get_recent_sales():
    with open('other/tracked_wallets.json', 'r') as f:
        tracked_wallets = json.load(f)
    wallet_addresses = list(tracked_wallets.keys())

    
    one_day_ago = int((datetime.now() - timedelta(days=7)).timestamp())
    print(one_day_ago)

    recent_sales = await get_recent_sales(wallet_addresses, from_timestamp=one_day_ago)
    parsed_transfers = parse_recent_sales_response(recent_sales)
    print(parsed_transfers)

if __name__ == "__main__":
    asyncio.run(test_get_recent_sales())