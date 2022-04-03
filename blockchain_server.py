from flask import Flask, jsonify, request

import blockchain
import wallet

app = Flask(__name__)

# database
cache = {}


@app.route('/chain', methods=['GET'])
def get_chain():
    block_chain = get_blockchain()
    response = {
        'chain': block_chain.chain,
    }
    return jsonify(response), 200


@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    block_chain = get_blockchain()
    if request.method == 'GET':
        transactions = block_chain.transaction_pool
        response = {
            'transactions': transactions,
            'length': len(transactions)
        }
        return jsonify(response), 200

    if request.method == 'POST':
        request_json = request.json
        required = (
            'sender_blockchain_address',
            'recipient_blockchain_address',
            'value',
            'sender_public_key',
            'signature'
        )
        if not all(k in request_json for k in required):
            return jsonify({'message': 'Missing values'}), 400

        is_created = block_chain.create_transaction(
            request_json['sender_blockchain_address'],  # type: ignore
            request_json['recipient_blockchain_address'],  # type: ignore
            request_json['value'],  # type: ignore
            request_json['sender_public_key'],  # type: ignore
            request_json['signature']  # type: ignore
        )

        if not is_created:
            return jsonify({'message': 'Error creating transaction'}), 400

        return jsonify({'message': 'Transaction created'}), 201


@app.route('/mine', methods=['GET'])
def mine():
    block_chain = get_blockchain()
    is_mined = block_chain.mining()
    if is_mined:
        return jsonify({'message': 'Success'}), 200

    return jsonify({'message': 'fail'}), 400


@app.route('/mine/start', methods=['GET'])
def start_mine():
    get_blockchain().start_mining()
    return jsonify({'message': 'Success'}), 200


def get_blockchain():
    cached_blokchain = cache.get('blockchain')
    if not cached_blokchain:
        miner_wallet = wallet.Wallet()
        cache['blockchain'] = blockchain.BlockChain(
            blockchain_address=miner_wallet.blockchain_address,
            port=app.config['port']
        )
        app.logger.warning({
            'private_key': miner_wallet.private_key,
            'public_key': miner_wallet.public_key,
            'blockchain_address': miner_wallet.blockchain_address
        })
    return cache['blockchain']


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port',
                        default=5010, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.config['port'] = port

    app.run(host='0.0.0.0', port=port, threaded=True, debug=True)
