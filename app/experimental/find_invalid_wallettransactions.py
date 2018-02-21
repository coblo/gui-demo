import app
app.init()

from app.backend.rpc import get_active_rpc_client
client = get_active_rpc_client()

i = 0
sum = 0
while True:
    wallet_txs = client.listwallettransactions(count=1000, skip=i, verbose=True)["result"]
    i += 1000
    if len(wallet_txs) == 0:
        break
    for wallet_tx in wallet_txs:
        if not wallet_tx["valid"]:
            continue
        sum += wallet_tx['balance']['amount']

print("real wallet", sum)