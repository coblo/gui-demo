# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from binascii import unhexlify
from datetime import datetime
from hashlib import sha256, new

import base58
permission_candidates = ['admin', 'mine', 'issue', 'create']

from app.responses import Getblockchaininfo
from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.enums import Stream
from app.helpers import init_logging, init_data_dir, batchwise
from app.models import Address, Permission, Transaction, VotingRound, init_profile_db, init_data_db, data_db, Block, \
    Profile
from app.tools.validators import is_valid_username

log = logging.getLogger(__name__)


def getinfo():
    """Update latest wallet balance on current profile"""
    client = get_active_rpc_client()
    profile = Profile.get_active()
    result = client.getinfo()['result']

    if result['balance'] != profile.balance:
        profile.balance = result['balance']
        profile.save()


def getblockchaininfo():
    """Emit headers and blocks (block sync status)"""
    client = get_active_rpc_client()
    result = client.getblockchaininfo()['result']
    # Todo: Maybe track headers/blocks on Profile db model
    signals.getblockchaininfo.emit(Getblockchaininfo(**result))


def getruntimeparams():
    """Update wallet main address on current profile"""
    client = get_active_rpc_client()
    profile = Profile.get_active()
    result = client.getruntimeparams()['result']

    if result['handshakelocal'] != profile.address:
        profile.address = result['handshakelocal']
        profile.save()


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
    if has_new:
        signals.listwallettransactions.emit()
    return has_new


def listpermissions():
    client = get_active_rpc_client()
    node_height = client.getblockcount()['result']

    perms = client.listpermissions()
    if not perms:
        log.warning('no permissions from api')
        return
    new_perms, new_votes = False, False

    Permission.delete().execute()

    admin_addresses = set()
    miner_addresses = set()

    with data_db.atomic():
        profile = Profile.get_active()

        for perm in perms['result']:
            perm_type = perm['type']
            perm_start = perm['startblock']
            perm_end = perm['endblock']

            if perm_type not in Permission.PERM_TYPES:
                continue

            if perm_type == Permission.ADMIN and perm_start < node_height < perm_end:
                admin_addresses.add(perm['address'])

            if perm_type == Permission.MINE and perm_start < node_height < perm_end:
                miner_addresses.add(perm['address'])

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

    new_is_admin = profile.address in admin_addresses
    if profile.is_admin != new_is_admin:
        profile.is_admin = new_is_admin

    new_is_miner = profile.address in miner_addresses
    if profile.is_miner != new_is_miner:
        profile.is_miner = new_is_miner

    if profile.dirty_fields:
        profile.save()

    # Todo: maybe only trigger table updates on actual change?
    signals.listpermissions.emit()  # triggers community tab updates
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

    client = get_active_rpc_client()

    # TODO read and process only fresh stream data by storing a state cursor between runs
    # TODO read stream items 100 at a time
    stream_items = client.liststreamitems(Stream.alias.name, count=100000)
    if not stream_items['result']:
        log.debug('got no items from stream alias')
        return 0

    by_addr = {}  # address -> alias
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

    # update database
    profile = Profile.get_active()
    new_main_alias = by_addr.get(profile.address)
    if new_main_alias and profile.alias != new_main_alias:
        log.debug('sync found new alias. profile.alias from %s to %s' % (profile.alias, new_main_alias))
        profile.alias = new_main_alias
        profile.save()

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


def sha256d(data):
    return sha256(sha256(data).digest()).digest()


def xor_bytes(a, b):
    result = bytearray()
    for b1, b2 in zip(a, b):
        result.append(b1 ^ b2)
    return bytes(result)


def otherToAddr(pubkey, pubkeyhash_version, checksum_value):
    # Work with raw bytes
    pubkey_raw = unhexlify(pubkey)
    pkhv_raw = unhexlify(pubkeyhash_version)
    cv_raw = unhexlify(checksum_value)

    # Hash public key
    ripemd160 = new('ripemd160')
    ripemd160.update(sha256(pubkey_raw).digest())
    pubkey_raw_hashed = ripemd160.digest()

    # Extend
    steps = 20 // len(pkhv_raw)
    chunks = [pubkey_raw_hashed[i:i + steps] for i in range(0, len(pubkey_raw_hashed), steps)]
    pubkey_raw_extended = b''
    for idx, b in enumerate(unhexlify(pubkeyhash_version), start=0):
        pubkey_raw_extended += b.to_bytes(1, 'big') + chunks[idx]

    # Double SHA256
    pubkey_raw_sha256d = sha256d(pubkey_raw_extended)

    # XOR first 4 bytes with address-checksum-value for postfix
    postfix = xor_bytes(pubkey_raw_sha256d[:4], cv_raw)

    # Compose final address
    address_bin = pubkey_raw_extended + postfix
    return base58.b58encode(address_bin)

def processTransaction(client, txid, pubkeyhash_version, checksum_value):
    transaction = client.getrawtransaction(txid, 4)
    if transaction['error'] is None:
        if 'vout' in transaction['result']:
            vout = transaction['result']['vout']
            permissions = []
            start_block = None
            end_block = None
            for vout_key, entry in enumerate(vout):
                if len(entry['permissions']) > 0:
                    for key, perm in entry['permissions'][0].items():
                        if perm and key in permission_candidates:
                            permissions.append(key)
                        if key == 'startblock':
                            start_block = perm
                        if key == 'endblock':
                            end_block = perm
                    in_entry = transaction['result']['vin'][vout_key]
                    public_key = in_entry['scriptSig']['asm'].split(' ')[1]
                    from_pubkey = otherToAddr(public_key, pubkeyhash_version, checksum_value)
                    given_to = entry['scriptPubKey']['addresses']
                    print(permissions, given_to, from_pubkey)


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

    blockchain_params = client.getblockchainparams()['result']
    pubkeyhash_version = blockchain_params['address-pubkeyhash-version']
    checksum_value = blockchain_params['address-checksum-value']

    for batch in batchwise(range(height_db, height_node), 100):

        new_blocks = client.listblocks(batch)

        with data_db.atomic():
            for block in new_blocks['result']:
                if block['txcount'] > 1:
                    height = block['height']
                    block_info = client.getblock("{}".format(height))['result']
                    for txid in block_info['tx']:
                        processTransaction(client, txid, pubkeyhash_version, checksum_value)

                addr_obj, adr_created = Address.get_or_create(address=block['miner'])
                block_obj, blk_created = Block.get_or_create(
                    hash=unhexlify(block['hash']),
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
    import app
    app.init()
    print(listblocks())
