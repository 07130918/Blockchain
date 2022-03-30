import hashlib
import json
import logging
import sys
import time

from ecdsa import VerifyingKey, NIST256p

import utils

# hash値の先頭の0数
MINNING_DIFFICULTY = 4
MINNING_SENDER = 'THE BLOCKCHAIN NETWORK'
MINNING_REWARD = 1.0

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


class BlockChain(object):

    def __init__(self, blockchain_address=None):
        self.transaction_pool = []
        self.chain = []
        # はじめは空のブロックを作っておく
        self.create_block(0, self.hash({}))
        self.blockchain_address = blockchain_address

    def create_block(self, nonce, previous_hash):
        block = utils.sorted_dict_by_key({
            'timestamp': time.time(),
            'transactions': self.transaction_pool,
            'nonce': nonce,
            'previous_hash': previous_hash
        })
        self.chain.append(block)
        self.transaction_pool = []
        return block

    def hash(self, block):
        """
        utils.sorted_dict_by_keyでもソートしていが再チェック
        ブロックからハッシュを生成する
        """
        sorted_block = json.dumps(block, sort_keys=True)
        return hashlib.sha256(sorted_block.encode()).hexdigest()

    def add_transaction(self, sender_blockchain_address,
                        recipient_blockchain_address, value,
                        sender_public_key=None, signature=None):
        transaction = utils.sorted_dict_by_key({
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'value': float(value)
        })
        if sender_blockchain_address == MINNING_SENDER:
            self.transaction_pool.append(transaction)
            return True

        if self.verify_transaction_signature(sender_public_key, signature, transaction):
            # if self.calculate_total_amount(sender_blockchain_address) < float(value):
            #     logger.error({'action': 'add_transaction', 'status': 'no_value_error'})
            #     return False

            self.transaction_pool.append(transaction)
            return True

        return False

    def verify_transaction_signature(self, sender_public_key, signature, transaction):
        """
        公開鍵、signature、transactionを使って、送金が正しいかを確認する
        """
        sha256 = hashlib.sha256()
        sha256.update(str(transaction).encode('utf-8'))
        message = sha256.digest()
        signature_bytes = bytes().fromhex(signature)
        verifying_key = VerifyingKey.from_string(
            bytes().fromhex(sender_public_key), curve=NIST256p)
        verified_key = verifying_key.verify(signature_bytes, message)
        return verified_key

    def proof_of_work(self):
        """ previous_hash,transaction,nonceでハッシュを生成し先頭に0が難易度分続くものが生まれればnonceを返す """
        transactions = self.transaction_pool.copy()
        previous_hash = self.hash(self.chain[-1])
        nonce = 0
        while self.valid_proof(transactions, previous_hash, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, transactions, previous_hash, nonce,
                    difficulty=MINNING_DIFFICULTY):
        """ ブロックのハッシュがdifficulty分0から始まるかを確認し、真偽値を返す """
        block = utils.sorted_dict_by_key({
            'transactions': transactions,
            'nonce': nonce,
            'previous_hash': previous_hash
        })
        return self.hash(block)[:difficulty] == '0' * difficulty

    def minning(self):
        # nonceを探す
        nonce = self.proof_of_work()
        self.add_transaction(
            sender_blockchain_address=MINNING_SENDER,
            recipient_blockchain_address=self.blockchain_address,
            value=MINNING_REWARD)
        # ブロックを作る
        # previous_hash: 前のブロックのハッシュ値
        previous_hash = self.hash(self.chain[-1])
        self.create_block(nonce, previous_hash)
        logger.info({'action': 'minning', 'status': 'success'})
        return True

    def calculate_total_amount(self, blockchain_address):
        total_amount = 0.0
        for block in self.chain:
            for transaction in block['transactions']:
                if blockchain_address == transaction['recipient_blockchain_address']:
                    total_amount += float(transaction['value'])
                if blockchain_address == transaction['sender_blockchain_address']:
                    total_amount -= float(transaction['value'])
        return total_amount
