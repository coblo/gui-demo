# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from datetime import datetime

from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.enums import Stream, SettingKey
from app.helpers import init_logging, init_data_dir
from app.models import Address, Permission, Transaction, VotingRound, init_profile_db, init_data_db, data_db
from app.settings import settings
from app.tools.validators import is_valid_username

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


def liststreamitems_alias():

    settings_main_alias = settings.value(SettingKey.alias.name, '', str)
    settings_main_address = settings.value(SettingKey.address.name, '', str)

    client = get_active_rpc_client()

    # TODO read and process only fresh stream data by storing a state cursor between runs
    # TODO read stream items 100 at a time
    stream_items = client.liststreamitems(Stream.alias.name, count=100000)
    if not stream_items['result']:
        log.debug('got no items from stream alias')
        return 0

    by_addr = {}     # address -> alias
    reseved = set()  # reserved aliases

    # aggregate the final state of address to alias mappings from stream
    for item in stream_items['result']:
        confirmations = item['confirmations']
        alias = item['key']
        address = item['publishers'][0]
        data = item['data']
        num_publishers = len(item['publishers'])

        # Sanity checks
        if confirmations < 1:
            log.debug('ignore alias - 0 confirmations for %s -> %s' % (address, alias))
            continue
        if data:
            log.debug('ignore alias - alias item "%s" with data "%s..."' % (alias, data[:8]))
            continue
        if not is_valid_username(alias):
            log.debug('ignore alias - alias does not match our regex: %s' % alias)
            continue
        if num_publishers != 1:
            log.debug('ignore alias - alias has multiple publishers: %s' % alias)
            continue
        if alias in reseved:
            log.debug('ignore alias - alias "%s" already reserved by "%s"' % (alias, address))
            continue

        is_new_address = address not in by_addr

        if is_new_address:
            by_addr[address] = alias
            reseved.add(alias)
            continue

        is_alias_change = by_addr[address] != alias

        if is_alias_change:
            log.debug('change alias of %s from %s to %s' % (address, by_addr[address], alias))
            # reserve new name
            reseved.add(alias)
            # release old name
            reseved.remove(by_addr[address])
            # set new name
            by_addr[address] = alias
            continue

    # signal alias to gui
    new_main_alias = by_addr.get(settings_main_address)
    if new_main_alias != settings_main_alias:
        signals.alias_changed.emit(new_main_alias)

    # update addresses in database
    with data_db.atomic():
        old_addrs = set(Address.select(Address.address, Address.alias).tuples())
        new_addrs = set(by_addr.items())
        # set of elements that are only in new_addr but not in old_addr
        changed_addrs = new_addrs - old_addrs
        new_rows = [dict(address=i[0], alias=i[1]) for i in changed_addrs]
        if new_rows:
            log.debug('adding new aliases %s' % changed_addrs)
            # insert rows 100 at a time.
            for idx in range(0, len(new_rows), 100):
                Address.insert_many(new_rows[idx:idx + 100]).upsert(True).execute()

    return len(changed_addrs)


if __name__ == '__main__':
    init_logging()
    init_data_dir()
    init_profile_db()
    init_data_db()
    # listwallettransactions()
    # listpermissions()
    print(liststreamitems_alias())
