# Blockchain

## blockchain.py
```
ブロックチェーンの概念に関するもの
マイニング等もここに記載
マイニング報酬は一応'THE BLOCKCHAIN NETWORK'から送金される.
トランザクションの証明
```

## wallet.py
```
仮想通貨ウォレット
bitcoin node側に投げるトランザクションの署名
```

## blockchain_server.py
```
python blockchain_server.pyで
block chain serverを起動できる。
localhost:5001, 5002, 5003
```

### blockchain_server API
```
/chain
    GET:
        ブロックチェーンを見れる。

/transactions
    GET:
        トランザクションプール返す。
    POST:
        トランザクションの作成。
    PUT:
        他のブロックチェーンサーバーがあればトランザクションの同期を行う。
    DELETE:
        トランザクションプールを空にする。

/mine
    GET:
        マイニングを行う

/mine/start
    GET:
        マイニングを行う(他のスレッドでマイニングが行われていない場合)
        (現状使っていない)

/consensus
    GET:
        他ノードから最も長いチェーンを探しあれば、同期する。

/amount
    GET:
        任意のブロックチェーンアドレスの残高を返す。

```

## wallet_server.py
```
python wallet_server.pyで
wallet serverを起動できる。
localhost:8080, 8081
```

### wallet_server API
```
/
    GET:
        トップページをレンダリング
        ページを開いた瞬間に/wallet にPOST

/wallet
    POST:
        ウォレットの作成

/transaction
    POST:
        フロントから来た送金に関するデータを受け取り、ブロックチェーンサーバーの`/transactions`に`POST`

/wallet/amount
    GET:
        ブロックチェーンサーバーの`/amount`に`GETリクエスト`を送り残高を取得
```
