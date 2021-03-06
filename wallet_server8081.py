import urllib.parse
from flask import Flask, jsonify, render_template, request
import requests

import wallet

app = Flask(__name__, template_folder='./templates')


@app.route('/')
def index():
    return render_template('./index.html')


@app.route('/wallet', methods=['POST'])
def create_wallet():
    my_wallet = wallet.Wallet()
    response = {
        'private_key': my_wallet.private_key,
        'public_key': my_wallet.public_key,
        'blockchain_address': my_wallet.blockchain_address
    }
    return jsonify(response), 200


@app.route('/transaction', methods=['POST'])
def create_transaction():
    """ フロントエンドから送金リクエストが来るのでそれをブロックチェーンのサーバーに投げる """
    request_json = request.json
    required = (
        'sender_private_key',
        'sender_blockchain_address',
        'recipient_blockchain_address',
        'sender_public_key',
        'value'
    )
    if not all(k in request_json for k in required):
        return 'Missing values', 400

    sender_private_key = request_json['sender_private_key']  # type: ignore
    # type: ignore
    sender_blockchain_address = request_json['sender_blockchain_address']
    # type: ignore
    recipient_blockchain_address = request_json['recipient_blockchain_address']
    sender_public_key = request_json['sender_public_key']  # type: ignore
    value = float(request_json['value'])  # type: ignore

    transaction = wallet.Transaction(
        sender_private_key,
        sender_public_key,
        sender_blockchain_address,
        recipient_blockchain_address,
        value
    )

    json_data = {
        'sender_blockchain_address': sender_blockchain_address,
        'recipient_blockchain_address': recipient_blockchain_address,
        'sender_public_key': sender_public_key,
        'value': value,
        'signature': transaction.generate_signature()
    }

    # blockchain gateway(blockchain_serverのtransactionメソッド)APIに送金リクエストを送る
    response = requests.post(
        urllib.parse.urljoin(app.config['gw'], 'transactions'),
        json=json_data,
        timeout=3
    )

    if response.status_code == 201:
        return jsonify({'message': 'Transaction created'}), 201
    else:
        return jsonify({'message': 'Error creating transaction', 'response': response}), 400


@app.route('/wallet/amount', methods=['GET'])
def calculate_amount():
    """ blockchain_serverの'/amount'にGETリクエストを送り残高を取得 """
    required = ['blockchain_address']
    if not all(k in request.args for k in required):
        return 'Missing values', 400

    my_blockchain_address = request.args.get(
        'blockchain_address')  # type: ignore
    response = requests.get(
        urllib.parse.urljoin(app.config['gw'], 'amount'),
        {'blockchain_address': my_blockchain_address},
        timeout=3
    )

    if response.status_code == 200:
        total = response.json()['amount']
        return jsonify({'message': 'success', 'amount': total}), 200
    else:
        return jsonify({'message': 'Error getting amount', 'response': response}), 400


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port',
                        default=8081, type=int, help='port to listen on')
    parser.add_argument('-g', '--gw', default='http://127.0.0.1:5001',
                        type=str, help='blockchain gateway')
    args = parser.parse_args()
    port = args.port
    app.config['gw'] = args.gw

    app.run(host='0.0.0.0', port=port, threaded=True, debug=True)
