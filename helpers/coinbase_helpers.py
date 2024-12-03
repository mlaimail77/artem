import os

from cdp import *

# Zora WOW Token Actions
from cdp_agentkit_core.actions.wow.create_token import *
from cdp_agentkit_core.actions.wow.buy_token import *
from cdp_agentkit_core.actions.wow.sell_token import *

# Core actions
from cdp_agentkit_core.actions.deploy_token import *
from cdp_agentkit_core.actions.register_basename import *
from cdp_agentkit_core.actions.trade import *
# from cdp_agentkit_core.actions.transfer import *


from dotenv import load_dotenv

load_dotenv('.env.local')

Cdp.configure(os.getenv('COINBASE_API_KEY_NAME'), os.getenv('COINBASE_API_KEY_PRIVATE_KEY'))

wallet_id = os.getenv('WALLET_ID_SEPOLIA')

def fetch_wallet(wallet_id, file_path):
    fetched_wallet = Wallet.fetch(wallet_id)
    fetched_wallet.load_seed(file_path=file_path)

    return fetched_wallet

def artto_setup():
    # Create a new wallet 
    # https://artto-ai-85.localcan.dev
    artto_wallet = Wallet.create(network_id="base-mainnet")
    print(f"Wallet successfully created: {artto_wallet}")

    address = artto_wallet.default_address
    print(f"Address: {address}")

    file_path = "artto_mainnet_seed.json"
    artto_wallet.save_seed(file_path, encrypt=True)
    print(f"Seed for wallet {artto_wallet.id} successfully saved to {file_path}.")

    artto_webhook = artto_wallet.create_webhook(os.getenv('ARTTO_COINBASE_WEBHOOK_URL'))

    #TODO(ADD EVENT TYPE: erc721_transfer)

    print(f"Webhook successfully created: {artto_webhook}")

if __name__ == "__main__":
    # artto_setup()

    wallet = fetch_wallet(os.getenv('WALLET_ID_SEPOLIA'), "artto_sepolia_seed.json")
    print(wallet.default_address)
    print(wallet.balances())

    transferFromArgs = {
        "from":"0xb8a20c24cB18c372e9f842d9E953A90ef2fe3640",
        "to":"0x9424116b9D61d04B678C5E5EddF8499f88ED9ADE",
        "tokenId":"18"
    }

    invoke_contract = wallet.invoke_contract(
        contract_address="0xFF19Ee09E029bBBD503f84b7f8dFb3F356a06b27",
        method="transferFrom",
        args=transferFromArgs,
        asset_id="TRUCHET"
    )

    invoke_contract.wait()

    # print(wallet.balances("0xFF19Ee09E029bBBD503f84b7f8dFb3F356a06b27"))
    # transfer = wallet.transfer(
    #     wallet=wallet,
    #     amount=0.00001,
    #     asset_id="eth",
    #     destination="0x9424116b9D61d04B678C5E5EddF8499f88ED9ADE"
    # )
    # 0xb8a20c24cB18c372e9f842d9E953A90ef2fe3640
    # transfer.wait()


