# Blockchain

### blockchain.py
ブロックチェーンの概念に関するもの
マイニング等もここに記載
マイニング報酬は一応'THE BLOCKCHAIN NETWORK'から送金される
トランザクションの証明

### wallet.py
仮想通貨ウォレット
bitcoin node側に投げるトランザクションの署名

### blockchain_server.py
python blockchain_server.pyで
block chain serverを起動できる。
localhost:5010/chain
    GET:
        ブロックチェーンを見れる。
localhost:5010/transactions
    GET:
        トランザクションプールを見れる。
    POST:
        トランザクションの作成。

### wallet_server.py
python wallet_server.pyで
wallet serverを起動できる。
localhost:8080
    GET:
        ページを開いた瞬間に/wallet にPOST
localhost:8080/wallet
    POST:
        ウォレットの作成。
localhost:8080/transaction
    POST:
        フロントから来た送金に関するデータを受け取り、ブロックチェーンサーバー(localhost:5010/transactions)にPOST
