import requests
from web3 import Web3
from web3 import Web3
from loguru import logger
from time import time
from threading import Thread
from eth_account import Account, messages
import json
import requests

goerly_url = "https://goerli.infura.io/v3/5710af96bc8b41eab2e4373d00094598"
flashbots_goerly = "https://relay-goerli.flashbots.net"

w3 = Web3(Web3.HTTPProvider(goerly_url))

FIRST_KEY = ""
SECOND_KEY = ""

flashbots_private_key = ""

first_account = Account.from_key(FIRST_KEY)
second_account = Account.from_key(SECOND_KEY)

print(first_account.address)
print(second_account.address)


MAIN_ACC = "0x791d7DaC9eC14e17536fD09fA938d14fe9746854"

tx = {
    "chainId": w3.eth.chain_id,
    "gas": 21000,
    "maxFeePerGas": Web3.to_wei(200, "gwei"),
    "maxPriorityFeePerGas": Web3.to_wei(5, "gwei"),
    "value": Web3.to_wei(0.01, 'ether'),
    "to": second_account.address,
    "nonce": w3.eth.get_transaction_count(first_account.address),
    "type": 2
}


signed_tx = w3.eth.account.sign_transaction(tx, FIRST_KEY)
w3.eth.send_raw_transaction(signed_tx.rawTransaction) # simulating random deposit on mev

second_tx = {
    "chainId": w3.eth.chain_id,
    "gas": 21000,
    "maxFeePerGas": Web3.to_wei(200, "gwei"),
    "maxPriorityFeePerGas": Web3.to_wei(5, "gwei"),
    "value": Web3.to_wei(0.001, 'ether'),
    "to": MAIN_ACC,
    "nonce": w3.eth.get_transaction_count(second_account.address),
    "type": 2
}

signed_raw = w3.eth.account.sign_transaction(second_tx, SECOND_KEY).rawTransaction


def send_bundle(incoming_tx_hash, send_tx, block_number):

        body_ = {
                "jsonrpc":"2.0","id":1,"method":"mev_sendBundle",
                "params": [
                    {
                    "version": "v0.1",
                    "inclusion": {
                        "block": str(Web3.to_hex(block_number)),
                        "maxBlock": str(Web3.to_hex(block_number + 1))
                    },
                    "body": [
                        {
                            "hash": incoming_tx_hash.hex()
                        },
                        {
                            "tx": send_tx.hex(),
                            "canRevert": False
                        }
                    ],
                    "validity": {
                        "refund": [],
                        "refundConfig": []
                    }
                    }
                ]
        }
        body = json.dumps(body_)

        message = messages.encode_defunct(text=Web3.keccak(text=body).hex())
        signature = (Account.from_key(flashbots_private_key).address) + ':' + Account.sign_message(message, flashbots_private_key).signature.hex()
        headers = {"Content-Type": "application/json", "X-Flashbots-Signature": signature}
        response = requests.post(flashbots_goerly, headers=headers, json=body_).json()

        print(f'Bundle Response: {response}')

        bundle_hash = response["result"]['bundleHash']
        return bundle_hash



while True:
    try:
        current_block = w3.eth.get_block_number()
        print(f'Current block: {current_block} | dist: {current_block + 1}')
        bundle = send_bundle(signed_tx.hash, signed_raw, current_block)
        break
    except: pass