import app
app.init()

from app.backend.rpc import get_active_rpc_client
client = get_active_rpc_client()

i = 0
finished = False
wallet_addresses = client.getaddresses(False)["result"]
while not finished:
    wallet_txs = client.listwallettransactions(count=100, skip=i, verbose=True)["result"]
    i += 100
    if len(wallet_txs) == 0:
        break
    for wallet_tx in wallet_txs:
        if not wallet_tx["valid"]:
            continue
        if wallet_tx.get("generated"):
            block = client.getblock(wallet_tx["blockhash"])["result"]
            if block["miner"] not in wallet_addresses:
                print(wallet_tx)
                print(block)
                print(wallet_tx['txid'] in block["tx"])