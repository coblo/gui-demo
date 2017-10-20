from datetime import datetime
from app.backend.rpc import client
txs = client.listwallettransactions(10000000)

balance = 0
for tx in txs['result']:
    if tx['valid']:
        txid = tx['txid']
        dt = datetime.fromtimestamp(tx['time'])
        description = tx.get('comment', '')
        perm = tx['permissions']
        if perm:
            description = 'Skills grant/revoke'

        items = tx['items']
        if items:
            first_item_type = items[0].get('type')
            if first_item_type == 'stream':
                description = 'Stream publishing'
        if tx.get('generated'):
            description = 'Mining reward'

        amount = tx['balance']['amount']
        balance += amount
        perm = tx['permissions']
        print(txid, dt, description, amount, balance)
