# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from datetime import datetime

from app.backend.rpc import get_active_rpc_client
from app.helpers import init_logging
from app.models import Transaction, init_profile_db, init_data_db, data_db

log = logging.getLogger(__name__)


def listwallettransactions():
    client = get_active_rpc_client()
    txs = client.listwallettransactions(10000000)
    if not txs:
        log.warning('no transactions from api')
        return
    balance = 0
    transactions = []
    has_new = False
    Transaction.delete().execute()
    with data_db.atomic():
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
                confirmations = tx['confirmations']

                tx_obj, created = Transaction.get_or_create(
                    txid=txid, defaults=dict(
                        datetime=dt,
                        comment=description,
                        amount=amount,
                        balance=balance,
                        confirmations=confirmations
                    )
                )
                if created:
                    has_new = True
                else:
                    tx_obj.save()
    return has_new


if __name__ == '__main__':
    init_logging()
    init_profile_db()
    init_data_db()
    listwallettransactions()
