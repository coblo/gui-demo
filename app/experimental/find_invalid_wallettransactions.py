import app
app.init()

from app.backend.rpc import get_active_rpc_client
client = get_active_rpc_client()

from app.models.db import data_session_scope
from app.models import WalletTransaction


sum = 0
with data_session_scope() as session:
    wtxs = session.query(WalletTransaction).all()
    for tx in wtxs:
        sum += tx.amount

print("db wallet", sum)

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