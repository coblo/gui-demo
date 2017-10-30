# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from datetime import datetime

from app.backend.rpc import get_active_rpc_client
from app.helpers import init_logging
from app.models import Address, Permission, Transaction, VotingRound, init_profile_db, init_data_db, data_db

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


def listpermissions():
    client = get_active_rpc_client()
    perms = client.listpermissions()
    if not perms:
        log.warning('no permissions from api')
        return
    new_perms, new_votes = False, False
    Permission.delete().execute()
    with data_db.atomic():
        for perm in perms['result']:
            perm_type = perm['type']
            if perm_type not in Permission.PERM_TYPES:
                continue
            addr_obj, created = Address.get_or_create(address=perm['address'])

            for vote in perm['pending']:
                start_block = vote['startblock']
                end_block = vote['endblock']
                approbations = len(vote['admins'])
                vote_obj, created = VotingRound.get_or_create(
                    address=addr_obj, perm_type=perm_type, start_block=start_block, end_block=end_block,
                    defaults=(dict(approbations=approbations, first_vote=datetime.now()))
                )
                vote_obj.set_vote_type()
                if created:
                    new_votes = True
                else:
                    vote_obj.save()

            start_block = perm['startblock']
            end_block = perm['endblock']
            perm_obj, created = Permission.get_or_create(
                address=addr_obj, perm_type=perm_type, defaults=dict(start_block=start_block, end_block=end_block)
            )
            if created:
                new_perms = True
            else:
                perm_obj.save()
    return {'new_perms': new_perms, 'new_votes': new_votes}


if __name__ == '__main__':
    init_logging()
    init_profile_db()
    init_data_db()
    listwallettransactions()
