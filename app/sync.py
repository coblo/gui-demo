# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from datetime import datetime

from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.enums import Stream, SettingKey
from app.helpers import init_logging, init_data_dir, batchwise
from app.models import Address, Permission, Transaction, VotingRound, init_profile_db, init_data_db, data_db, Block
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

    is_admin_old = settings.value(SettingKey.is_admin.name, False, bool)
    is_miner_old = settings.value(SettingKey.is_miner.name, False, bool)

    is_admin_new = False
    is_miner_new = False

    users_address = settings.value(SettingKey.address.name)

    Permission.delete().execute()

    with data_db.atomic():

        for perm in perms['result']:
            perm_type = perm['type']
            if perm_type not in Permission.PERM_TYPES:
                continue

            if perm_type == Permission.ADMIN and users_address == perm['address']:
                is_admin_new = True

            if perm_type == Permission.MINE and users_address == perm['address']:
                is_miner_new = True

            addr_obj, created = Address.get_or_create(address=perm['address'])

            for vote in perm['pending']:
                start_block = vote['startblock']
                end_block = vote['endblock']
                approbations = len(vote['admins'])
                # TODO: Fix: current time of syncing is not the time of first_vote!
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
            # TODO Why get_or_create ... we just deleted all Permission objects
            perm_obj, created = Permission.get_or_create(
                address=addr_obj, perm_type=perm_type, defaults=dict(start_block=start_block, end_block=end_block)
            )
            if created:
                new_perms = True
            else:
                perm_obj.save()
        if is_admin_old != is_admin_new:
            settings.setValue(SettingKey.is_admin.name, is_admin_new)
            settings.sync()
            signals.is_admin_changed.emit(is_admin_new)
        if is_miner_old != is_miner_new:
            settings.setValue(SettingKey.is_miner.name, is_miner_new)
            settings.sync()
            signals.is_miner_changed.emit(is_miner_new)

    return {'new_perms': new_perms, 'new_votes': new_votes}


def liststreamitems_alias():
    """
    Sample stream item (none verbose):
    {
        'blocktime': 1505905511,
        'confirmations': 28948,
        'data': '4d696e65722031',
        'key': 'Miner_1',
        'publishers': ['1899xJpqZN3kMQdpvTxESWqykxgFJwRddCE4Tr'],
        'txid': 'caa1155e719803b9f39096860519a5e08e78214245ae9822beeea2b37a656178'
    }
    """

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


def listblocks() -> int:
    """Synch block data from node

    :return int: number of new blocks synched to database
    """

    # TODO: Handle blockchain forks gracefully

    client = get_active_rpc_client()

    height_node = client.getblockcount()['result']
    latest_block_obj = Block.select().order_by(Block.height.desc()).first()
    if latest_block_obj is None:
        height_db = 0
    else:
        height_db = latest_block_obj.height

    if height_db == height_node:
        return 0

    synced = 0

    for batch in batchwise(range(height_db, height_node), 100):

        new_blocks = client.listblocks(batch)

        with data_db.atomic():
            for block in new_blocks['result']:
                addr_obj, adr_created = Address.get_or_create(address=block['miner'])
                block_obj, blk_created = Block.get_or_create(
                    hash=block['hash'],
                    defaults=dict(
                        time=datetime.fromtimestamp(block['time']),
                        miner=addr_obj,
                        txcount=block['txcount'],
                        height=block['height'],
                    )
                )
                if blk_created:
                    synced += 1
                log.debug('Synced block {}'.format(block_obj.height))

    log.debug('Synced {} blocks total.'.format(synced))
    return synced


if __name__ == '__main__':
    init_logging()
    init_data_dir()
    init_profile_db()
    init_data_db()
    # listwallettransactions()
    listpermissions()
    liststreamitems_alias()
    print(listblocks())
