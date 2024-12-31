import os
import time

from cdp import *

# # Zora WOW Token Actions
# from cdp_agentkit_core.actions.wow import create_token, buy_token


from dotenv import load_dotenv

load_dotenv('.env.local')

Cdp.configure(os.getenv('COINBASE_API_KEY_NAME'), os.getenv('COINBASE_API_KEY_PRIVATE_KEY'))

wallet_id_sepolia = os.getenv('WALLET_ID_SEPOLIA')
wallet_id_mainnet = os.getenv('WALLET_ID_MAINNET')

wallet_sepolia = Wallet.fetch(wallet_id_sepolia)
wallet_mainnet = Wallet.fetch(wallet_id_mainnet)

file_path_sepolia = "artto_sepolia_seed.json"
file_path_mainnet = "artto_mainnet_seed.json"
wallet_sepolia.load_seed(file_path=file_path_sepolia)
wallet_mainnet.load_seed(file_path=file_path_mainnet)

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

def get_abi(network_id, contract_address):
    import requests
    import json

    base_url = f"https://{'api-sepolia' if network_id == 'base-sepolia' else 'api'}.basescan.org/api"
    params = {
        "module": "contract",
        "action": "getabi", 
        "address": contract_address,
        "apikey": os.getenv('BASESCAN_API_KEY')
    }

    response = requests.get(base_url, params=params)
    response_json = response.json()

    if response_json["status"] == "1" and response_json["message"] == "OK":
        abi = json.loads(response_json["result"])
    else:
        abi = None
    return abi

def get_implementation_address(network_id, contract_address):
    abi = get_abi(network_id, contract_address)
    invoke_contract = wallet.invoke_contract(
        contract_address=contract_address,
        method="implementation",
        abi=abi,
    )
    invoke_contract.wait()
    print(invoke_contract)

def register_llc(wallet, network_id, contract_address, proxy_address):
    abi = get_abi(network_id, proxy_address)
    invoke_contract = wallet.invoke_contract(
        contract_address=contract_address,
        method="createSeries", 
        abi=abi,
        amount=0.01312070788843195,
        args={"jurisdiction":"1", 
              "controller":wallet.default_address.address_id,
              "name": "ArttoLLC"}
        )
    invoke_contract.wait()
    return invoke_contract

def transfer_artto_token(wallet, token_amount, destination):

    artto_token_proxy_address = "0xcfc2de7f39a9e1460dd282071a458e02372e1f67"
    artto_token_address = "0x9239e9F9E325E706EF8b89936eCe9d48896AbBe3"

    abi = get_abi("base-mainnet", artto_token_proxy_address)

    value_to_transfer = token_amount * 10**18

    print(f"Transferring {token_amount} tokens with value {value_to_transfer}")
    max_attempts = 3
    attempt = 0
    delay = 10  # Initial delay in seconds
    last_error = None
    
    while attempt < max_attempts:
        try:
            transfer = wallet.invoke_contract(
                contract_address=artto_token_address,
                method="transfer",
                abi=abi,
                args={"to":destination, "value":str(int(value_to_transfer))}
            )
            transfer.wait()
            return f"Successfully transferred {token_amount} tokens to {destination}"
        except Exception as e:
            last_error = e
            attempt += 1
            if attempt == max_attempts:
                return f"Error transferring tokens after {max_attempts} attempts: {str(last_error)}"
            time.sleep(delay)
            delay *= 2  # Double delay for next attempt (10->20->40)

def transfer_erc1155(wallet, network_id, contract_address, from_address, to_address, token_id):
    try:
        print("Trying to transfer NFT")
        abi = get_abi(network_id, contract_address)
        invoke_contract = wallet.invoke_contract(
            contract_address=contract_address,
            method="safeTransferFrom", 
            abi=abi,
            args={"from":from_address, "to":to_address, "tokenId":token_id, "amount":1}
        )
        invoke_contract.wait()
        return f"Successfully transferred NFT {token_id} from {from_address} to {to_address}"
    except Exception as first_error:
        print(f"Error transferring NFT: {str(first_error)}")
        print("Trying again with implementation contract")
        try:
            # If first attempt fails, try getting implementation contract
            implementation_contract = SmartContract.read(
                network_id=network_id,
                contract_address=contract_address,
                method="implementation",
                abi=abi
            )
            
            # Get ABI of implementation contract
            implementation_abi = get_abi(network_id, implementation_contract)
            
            # Try transfer with implementation contract ABI but proxy address
            invoke_contract = wallet.invoke_contract(
                contract_address=contract_address,
                method="safeTransferFrom",
                abi=implementation_abi, 
                args={"from":from_address, "to":to_address, "tokenId":token_id, "amount":1}
            )
            invoke_contract.wait()
            return f"Successfully transferred NFT {token_id} from {from_address} to {to_address}"
        except Exception as e:
            error_msg = f"Error transferring NFT: {str(e)}"
            if hasattr(e, 'api_message'):
                error_msg += f" - {e.api_message}" 
            return error_msg



def transfer_erc721(wallet, network_id, contract_address, from_address, to_address, token_id):
    try:
        print("Trying to transfer NFT")
        abi = get_abi(network_id, contract_address)
        invoke_contract = wallet.invoke_contract(
            contract_address=contract_address,
            method="transferFrom", 
            abi=abi,
            args={"from":from_address, "to":to_address, "tokenId":token_id}
        )
        invoke_contract.wait()
        return f"Successfully transferred NFT {token_id} from {from_address} to {to_address}"
    except Exception as first_error:
        print(f"Error transferring NFT: {str(first_error)}")
        print("Trying again with implementation contract")
        try:
            # If first attempt fails, try getting implementation contract
            implementation_contract = SmartContract.read(
                network_id=network_id,
                contract_address=contract_address,
                method="implementation",
                abi=abi
            )
            
            # Get ABI of implementation contract
            implementation_abi = get_abi(network_id, implementation_contract)
            
            # Try transfer with implementation contract ABI but proxy address
            invoke_contract = wallet.invoke_contract(
                contract_address=contract_address,
                method="transferFrom",
                abi=implementation_abi, 
                args={"from":from_address, "to":to_address, "tokenId":token_id}
            )
            invoke_contract.wait()
            return f"Successfully transferred NFT {token_id} from {from_address} to {to_address}"
        except Exception as e:
            error_msg = f"Error transferring NFT: {str(e)}"
            if hasattr(e, 'api_message'):
                error_msg += f" - {e.api_message}" 
            return error_msg


# def launch_artto_token(wallet):

#     response = create_token.wow_create_token(
#         wallet=wallet,
#         name="Artto AI",
#         symbol="ARTTO",
#         token_uri="https://brown-mushy-crayfish-236.mypinata.cloud/ipfs/bafkreifkftdybmwgfaefsn4zjp4dakplb4wxnzobduwhxa4fhbzlisi4pq"
#     )
#     return response

if __name__ == "__main__":
    # artto_setup()
    wallet = fetch_wallet(os.getenv('WALLET_ID_MAINNET'), "artto_mainnet_seed.json")

    # print(wallet.default_address.balance(asset_id="0x9239e9F9E325E706EF8b89936eCe9d48896AbBe3"))

    # abi = get_abi("base-mainnet", "0xe970aC680342aFf70BB8D90A4C602D70f4405637")
    # implementation_contract = SmartContract.read(
    #     network_id="base-mainnet",
    #     contract_address="0xe970aC680342aFf70BB8D90A4C602D70f4405637",
    #     method="implementation",
    #     abi=abi
    # )

        # trade_result = wallet.trade(
    #         amount=0.02, from_asset_id="eth", to_asset_id=WETH_CONTRACT_BASE
    #     ).wait()
    # print(trade_result)

    # transfer = transfer_erc721(
    #     wallet=wallet,
    #     network_id="base-mainnet",
    #     contract_address="0xe970aC680342aFf70BB8D90A4C602D70f4405637",
    #     from_address="0x4e64c721eBBE3285CFA60b61a3E12a8f4E1709E8",
    #     to_address="0x9424116b9D61d04B678C5E5EddF8499f88ED9ADE",
    #     token_id="4")
    # print(transfer)


    # transfer = transfer_artto_token(wallet, 1, "0x9424116b9D61d04B678C5E5EddF8499f88ED9ADE")
    # print(transfer)

    # transfer.wait()

    # print(transfer)

    # print(wallet.default_address.balance(asset_id="0x9239e9F9E325E706EF8b89936eCe9d48896AbBe3"))




    # response = transfer(
    #     wallet=wallet,
    #     amount="1",
    #     asset_id="0x9239e9F9E325E706EF8b89936eCe9d48896AbBe3",
    #     destination="0x9424116b9D61d04B678C5E5EddF8499f88ED9ADE",
    #     gasless=True
    # )

    # print(wallet.default_address.balance(asset_id="0x9239e9F9E325E706EF8b89936eCe9d48896AbBe3"))
    # response = buy_token.wow_buy_token(
    #     wallet=wallet,
    #     contract_address="0x9239e9f9e325e706ef8b89936ece9d48896abbe3",
    #     amount_eth_in_wei=500000000000000000
    # )
    # print(response)


    # response = launch_artto_token(wallet)
    # print(response)



    # abi = get_abi("base-mainnet", "0xcfc2de7f39a9e1460dd282071a458e02372e1f67")
    # invoke_contract = wallet.invoke_contract(
    #     contract_address="0x1c197beEE1Dea08e40B49a0DF6926d0C4dBb0aCf",
    #     method="_tokenURI",
    #     abi=abi, 
    #     args={"_tokenURI":"https://brown-mushy-crayfish-236.mypinata.cloud/ipfs/bafkreibml4xkekojnrhyepyorsfixjk5yg3532m3cb4l3nkjfsi7lnkssq"}
    # )
    # invoke_contract.wait()
    # print(invoke_contract)


    # response = register_llc(wallet=wallet,
    #              network_id="base-mainnet", 
    #              contract_address="0x0d3BC598F0F75590CD75D60D40e0510F515EBE51", 
    #              proxy_address="0x66ef60f480A269F5e1e358699DD774180B2Fa8eE")
    
    # print(response)
    
    # response = transfer_nft(wallet=wallet,
    #              network_id="base-mainnet", 
    #              contract_address="0x3d8683Bbf9CaE7ad0441b65ddCadEC3850d1256E", 
    #              from_address=wallet.default_address.address_id, 
    #              to_address="0x9424116b9D61d04B678C5E5EddF8499f88ED9ADE", 
    #              token_id="8359")
    
    # print(response)


