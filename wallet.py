import binascii
import codecs
import base58
from ecdsa import SigningKey, NIST256p
import hashlib

import utils


class Wallet(object):

    def __init__(self):
        """ 公開鍵、秘密鍵を生成する """
        self._private_key = SigningKey.generate(curve=NIST256p)
        self._public_key = self._private_key.get_verifying_key()
        self._blockchain_address = self.generate_blockchain_address()

    @property
    def private_key(self):
        return self._private_key.to_string().hex()

    @property
    def public_key(self):
        return self._public_key.to_string().hex()

    @property
    def blockchain_address(self):
        return self._blockchain_address

    def generate_blockchain_address(self):
        # 公開鍵からSHA-256のアルゴリズムでハッシュを生成する
        public_key_bytes = self._public_key.to_string()
        sha256_bpk = hashlib.sha256(public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()

        # SHA-256からRipemdの短いハッシュを生成する(サーバーの負担を軽減するため)
        ripemd160_bpk = hashlib.new('ripemd160')
        ripemd160_bpk.update(sha256_bpk_digest)
        ripemd160_bpk_digest = ripemd160_bpk.digest()
        ripemd160_bpk_hex = codecs.encode(ripemd160_bpk_digest, 'hex')

        # network byteを足す
        network_byte = b'00'
        network_bitcoin_public_key = network_byte + ripemd160_bpk_hex
        network_bitcoin_public_key_bytes = codecs.decode(network_bitcoin_public_key,
                                                         'hex')

        # ダブルハッシュを生成する
        sha256_bpk = hashlib.sha256(network_bitcoin_public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()
        sha256_2_nbpk = hashlib.sha256(sha256_bpk_digest)
        sha256_2_nbpk_digest = sha256_2_nbpk.digest()
        sha256_hex = codecs.encode(sha256_2_nbpk_digest, 'hex')

        # Get checksum(データ整合性を確認)
        checksum = sha256_hex[:8]

        # publickeyとchecksumを足す
        address_hex = (network_bitcoin_public_key + checksum).decode('utf-8')

        # base58エンコードする
        blockchain_address = base58.b58encode(binascii.unhexlify(address_hex)).decode('utf-8')
        return blockchain_address


class Transaction(object):
    """
    Signatureは、公開鍵,秘密鍵,transactions
    (sender_blockchain_address,recipient_blockchain_address, value)
    を使いアルゴリズムに通すことで生成される
    """

    def __init__(self, sender_private_key, sender_public_key, sender_blockchain_address,
                 recipient_blockchain_address, value):
        self.sender_private_key = sender_private_key
        self.sender_public_key = sender_public_key
        self.sender_blockchain_address = sender_blockchain_address
        self.recipient_blockchain_address = recipient_blockchain_address
        self.value = value

    def generate_signature(self):
        sha256 = hashlib.sha256()
        transaction = utils.sorted_dict_by_key({
            'sender_blockchain_address': self.sender_blockchain_address,
            'recipient_blockchain_address': self.recipient_blockchain_address,
            'value': float(self.value)
        })
        sha256.update(str(transaction).encode('utf-8'))
        message = sha256.digest()
        private_key = SigningKey.from_string(
            bytes().fromhex(self.sender_private_key), curve=NIST256p)
        private_key_sign = private_key.sign(message)
        signature = private_key_sign.hex()
        return signature


if __name__ == '__main__':
    wallet_M = Wallet()
    wallet_A = Wallet()
    wallet_B = Wallet()
    t = Transaction(wallet_A.private_key, wallet_A.public_key,
                    wallet_A.blockchain_address, wallet_B.blockchain_address, 0.1)

    # Blockchain Node
    import blockchain
    blockchain = blockchain.BlockChain(
        blockchain_address=wallet_M.blockchain_address)
    is_added = blockchain.add_transaction(
        wallet_A.blockchain_address,
        wallet_B.blockchain_address,
        0.1,
        wallet_A.public_key,
        t.generate_signature()
    )
    print(is_added)
    blockchain.mining()
    utils.pprint(blockchain.chain)

    print('A', blockchain.calculate_total_amount(wallet_A.blockchain_address))
