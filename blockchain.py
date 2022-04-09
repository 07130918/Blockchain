import contextlib
import hashlib
import json
import logging
import sys
import time
import threading

from ecdsa import NIST256p, VerifyingKey
import requests

import utils

# hash値の先頭の0数
MINING_DIFFICULTY = 4
MINING_SENDER = 'THE BLOCKCHAIN NETWORK'
MINING_REWARD = 1.0
MINING_TIMER_SEC = 20

BLOCKCHAIN_PORT_RANGE = (5001, 5004)
NEIGHBOURS_IP_RANGE_NUM = (0, 1)
BLOCKCHAIN_NEIGHBOURS_SYNC_TIME_SEC = 20

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


class BlockChain(object):

    def __init__(self, blockchain_address=None, port=None):
        self.transaction_pool = []
        self.chain = []

        self.neighbours = []
        # はじめは空のブロックを作っておく
        self.create_block(0, self.hash({}))
        self.blockchain_address = blockchain_address
        self.port = port
        self.mining_semaphore = threading.Semaphore(1)
        self.sync_neighbours_semaphore = threading.Semaphore(1)

    def create_block(self, nonce, previous_hash):
        """
        新しくブロックを作り、チェーンに繋げる
        ブロックは,timestamp, transactions, nonce, previous_hash(前のブロックのハッシュ値)の4要素から成る
        """
        block = utils.sorted_dict_by_key({
            'timestamp': time.time(),
            'transactions': self.transaction_pool,
            'nonce': nonce,
            'previous_hash': previous_hash
        })
        self.chain.append(block)
        # トランザクションはブロックに詰め終わったため空にする
        self.transaction_pool = []
        # 他のnodeのプールも空にする
        for node in self.neighbours:
            requests.delete(f'http://{node}/transactions')

        return block

    def run(self):
        self.sync_neighbours()
        self.resolve_conflicts()
        # self.start_mining()

    def sync_neighbours(self):
        is_acquire = self.sync_neighbours_semaphore.acquire(blocking=False)
        if is_acquire:
            with contextlib.ExitStack() as stack:
                stack.callback(self.sync_neighbours_semaphore.release)
                self.set_neighbours()
                loop = threading.Timer(
                    BLOCKCHAIN_NEIGHBOURS_SYNC_TIME_SEC, self.sync_neighbours
                )
                loop.start()

    def set_neighbours(self):
        self.neighbours = utils.find_neighbours(
            utils.get_host(),
            self.port,
            NEIGHBOURS_IP_RANGE_NUM[0], NEIGHBOURS_IP_RANGE_NUM[1],
            BLOCKCHAIN_PORT_RANGE[0], BLOCKCHAIN_PORT_RANGE[1]
        )
        logger.info({'action': 'set_neighbours', 'neighbours': self.neighbours})

    def resolve_conflicts(self):
        """ 最も長いチェーンを採用するアルゴリズム """
        longest_chain = None
        max_length = len(self.chain)
        for node in self.neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                chain_length = len(chain)
                if chain_length > max_length and self.valid_chain(chain):
                    max_length = chain_length
                    longest_chain = chain

        if longest_chain:
            self.chain = longest_chain
            logger.info({'action': 'resolve_conflict', 'status': 'chain was replaced'})
            return True

        logger.info({'action': 'resolve_conflict', 'status': 'chain was not replaced'})
        return False

    def hash(self, block):
        """
        utils.sorted_dict_by_keyでもソートしていが再チェック
        ブロックからハッシュを生成する
        """
        sorted_block = json.dumps(block, sort_keys=True)
        return hashlib.sha256(sorted_block.encode()).hexdigest()

    def create_transaction(self, sender_blockchain_address,
                           recipient_blockchain_address, value,
                           sender_public_key, signature):
        is_transacted = self.add_transaction(sender_blockchain_address,
                                             recipient_blockchain_address, value,
                                             sender_public_key, signature)

        # 他のノードにトランザクションを同期させる
        if is_transacted:
            for node in self.neighbours:
                requests.put(
                    f'http://{node}/transactions',
                    json={
                        'sender_blockchain_address': sender_blockchain_address,
                        'recipient_blockchain_address': recipient_blockchain_address,
                        'value': value,
                        'sender_public_key': sender_public_key,
                        'signature': signature,
                    }
                )
        return is_transacted

    def add_transaction(self, sender_blockchain_address,
                        recipient_blockchain_address, value,
                        sender_public_key=None, signature=None):
        transaction = utils.sorted_dict_by_key({
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'value': float(value)
        })
        if sender_blockchain_address == MINING_SENDER:
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
        公開鍵、signature、transactionを使って、送金リクエストが正しいかを確認する
        bool値を返す
        """
        sha256 = hashlib.sha256()
        sha256.update(str(transaction).encode('utf-8'))
        message = sha256.digest()
        signature_bytes = bytes().fromhex(signature)
        verifying_key = VerifyingKey.from_string(
            bytes().fromhex(sender_public_key), curve=NIST256p)
        verified_key = verifying_key.verify(signature_bytes, message)
        return verified_key

    def mining(self):
        """ マイニング(ナンスを見つけ、新たなブロックを作る)を行う """
        if not self.transaction_pool:
            return False

        self.add_transaction(
            sender_blockchain_address=MINING_SENDER,
            recipient_blockchain_address=self.blockchain_address,
            value=MINING_REWARD)
        # nonceを探す
        nonce = self.proof_of_work()
        # ブロックを作る(previous_hash: 前のブロックのハッシュ値)
        previous_hash = self.hash(self.chain[-1])
        self.create_block(nonce, previous_hash)
        logger.info({'action': 'mining', 'status': 'mining success'})

        # 他のノードのブロックチェーンを更新する
        for node in self.neighbours:
            requests.put(f'http://{node}/consensus')

        return True

    def start_mining(self):
        is_acquire = self.mining_semaphore.acquire(blocking=False)
        # miningが実行中でなければ実行
        if is_acquire:
            with contextlib.ExitStack() as stack:
                stack.callback(self.mining_semaphore.release)
                self.mining()
                loop = threading.Timer(MINING_TIMER_SEC, self.start_mining)
                loop.start()

    def proof_of_work(self):
        """
        previous_hash,transaction,nonceでハッシュを生成し先頭に0が難易度分続くものが生まれればnonceを返す
        bitcoinは,proof of workのアルゴリズムを採用している
        """
        transactions = self.transaction_pool.copy()
        previous_hash = self.hash(self.chain[-1])
        nonce = 0
        while self.valid_proof(transactions, previous_hash, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, transactions, previous_hash, nonce,
                    difficulty=MINING_DIFFICULTY):
        """ ブロックのハッシュがdifficulty分0から始まるかを確認し、真偽値を返す """
        block = utils.sorted_dict_by_key({
            'transactions': transactions,
            'nonce': nonce,
            'previous_hash': previous_hash
        })
        return self.hash(block)[:difficulty] == '0' * difficulty

    def valid_chain(self, chain):
        """ ブロックチェーンが正しいかを(前のブロックのハッシュとnonceを用い)確認する """
        pre_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            # ブロックのハッシュが正しいかを確認
            if block['previous_hash'] != self.hash(pre_block):
                return False
            # ブロックのnonceが正しいかを確認
            if not self.valid_proof(block['transactions'], block['previous_hash'],
                                    block['nonce'], MINING_DIFFICULTY):
                return False
            pre_block = block
            current_index += 1
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
