# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from binascii import unhexlify
from datetime import datetime

import ubjson

from app import enums
from app.models import Alias
from app.models import MiningReward
from app.models.timestamp import Timestamp
from app.models.vote import Vote
from app.tools.address import public_key_to_address
from app.responses import Getblockchaininfo
from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.enums import Stream
from app.helpers import batchwise
from app.models import Address, Permission, Transaction, PendingVote, data_db, Block, Profile
from app.tools.validators import is_valid_username

log = logging.getLogger(__name__)

permission_candidates = ['admin', 'mine', 'issue', 'create']


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
    return result


def getruntimeparams():
    """Update wallet main address on current profile"""
    client = get_active_rpc_client()
    profile = Profile.get_active()
    result = client.getruntimeparams()['result']

    if result['handshakelocal'] != profile.address:
        profile.address = result['handshakelocal']
        profile.save()


def process_blocks():
    """
    Find last valid Block, delete every Block above in DB and get all Blocks above from Node.
    Process through new Blocks:
    Add them to DB.
    Process through all transactions in block.
    """
    client = get_active_rpc_client()

    ### get last valid block in DB ###
    last_valid_height = -1
    last_block_is_valid = False
    while not last_block_is_valid:
        if data_db().query(Block).count() == 0:
            break
        latest_block = data_db().query(Block).order_by(Block.height.desc()).first()
        try:
            block_from_chain = client.getblock(hash_or_height='{}'.format(latest_block.height))['result']
        except Exception as e:
            log.debug(e)
            return
        if latest_block.hash == unhexlify(block_from_chain['hash']):
            last_block_is_valid = True
            last_valid_height = latest_block.height
        else:
            data_db().delete(latest_block)

    ### process new blocks ###
    block_count_node = client.getblockcount()['result']
    for batch in batchwise(range(last_valid_height+1, block_count_node), 100):
        try:
            answer = client.listblocks(batch)
            if answer['error'] is None:
                new_blocks = answer['result']
            else:
                log.debug(answer['error'])
                return
        except Exception as e:
            log.debug(e)
            return

        for block in new_blocks:
            block_obj = Block(
                hash = unhexlify(block['hash']),
                height=block['height'],
                time=datetime.fromtimestamp(block['time']),
            )
            data_db().add(block_obj)
            if process_transactions(block['height']):
                data_db().commit()
            else:
                data_db().rollback()
                return
    if last_valid_height != block_count_node:
        process_permissions()


def process_transactions(block_height):
    client = get_active_rpc_client()

    try:
        block = client.getblock(hash_or_height='{}'.format(block_height))['result']
    except Exception as e:
        log.debug(e)
        return False
    for pos_in_block, txid in enumerate(block['tx']):
        try:
            tx = client.getrawtransaction(txid, 4)
            if tx["error"]:
                log.debug(tx["error"])
                continue
            tx_relevant = process_vouts(tx["result"], block['miner'])

        except Exception as e:
            log.debug(e)
            return False
        if tx_relevant:
            Transaction.create_if_not_exists(
                Transaction(
                    txid=txid,
                    pos_in_block=pos_in_block,
                    block=unhexlify(block['hash'])
                )
            )
    return True


def process_vouts(raw_transaction, miner) -> bool: #todo: better name
    relevant = False
    txid = raw_transaction["txid"]
    # mining reward
    for vin in raw_transaction["vin"]:
        if 'coinbase' in vin:
            relevant = True
            data_db().add(MiningReward(
                txid=txid,
                address=miner
            ))
    for vout in raw_transaction["vout"]:
        for item in vout["items"]:
            # stream item
            if item["type"] == "stream":
                publishers = item["publishers"]
                for publisher in publishers:
                    Address.create_if_not_exists(publisher)
                if item["name"] == "timestamp":
                    relevant = True
                    comment = ''
                    for entry in raw_transaction['data']:
                        data = ubjson.loadb(unhexlify(entry))
                        if 'comment' in data:
                            comment += data.get('comment', '')
                    data_db().add(Timestamp(
                        txid=txid,
                        hash=item["key"],
                        comment=comment,
                        address=publishers[0]
                    ))
                elif item['name'] == "alias":
                    alias = item["key"]
                    # Sanity checks
                    if item["data"] or not is_valid_username(alias) or len(publishers) != 1:
                        continue
                    relevant = True
                    data_db().add(Alias(
                        txid=txid,
                        address=publishers[0],
                        alias=alias
                    ))
            # mining reward
            # vote
            # wallet transactions?? oder batch wise extra holen?
    return relevant


def process_permissions():
    # todo: check if we have new perms / votes
    client = get_active_rpc_client()

    try:
        perms = client.listpermissions()['result']
    except Exception as e:
        log.debug(e)
        return

    data_db().query(Permission).delete()
    data_db().query(PendingVote).delete()

    for perm in perms:
        perm_type = perm['type']
        perm_start = perm['startblock']
        perm_end = perm['endblock']
        address = perm['address']

        Address.create_if_not_exists(address)

        if perm_type not in [enums.ISSUE, enums.CREATE, enums.MINE, enums.ADMIN]:
            continue

        perm_obj = Permission(
            address=address,
            perm_type=perm_type,
            start_block=perm_start,
            end_block=perm_end
        )
        data_db().add(perm_obj)
        data_db().commit()

        for vote in perm['pending']:
            start_block = vote['startblock']
            end_block = vote['endblock']
            # If candidate has already the permission continue.
            if start_block == perm['startblock'] and end_block == perm['endblock']:
                continue
            for admin in vote['admins']:
                Address.create_if_not_exists(admin)
                vote_obj = PendingVote(
                    address_from=admin,
                    address_to=address,
                    perm_type=perm_type,
                    start_block=start_block,
                    end_block=end_block
                )
                data_db().add(vote_obj)
                data_db().commit()


def listwallettransactions():
    pass
#     client = get_active_rpc_client()
#     txs = client.listwallettransactions(10000000)
#     if not txs:
#         log.warning('no transactions from api')
#         return
#     balance = 0
#     new_transactions = []
#     new_confirmations = []
#     with data_db.atomic():
#         for tx in txs['result']:
#             if tx['valid']:
#                 txid = tx['txid']
#                 dt = datetime.fromtimestamp(tx['time'])
#
#                 comment = ''
#                 txtype = Transaction.PAYMENT
#                 if tx['permissions']:
#                     txtype = Transaction.VOTE
#
#                 items = tx['items']
#                 if items:
#                     first_item = items[0]
#                     if first_item['type'] == 'stream':
#                         txtype = Transaction.PUBLISH
#                         comment = 'Stream:"' + first_item['name'] + '", Key: "' + first_item['key'] + '"'
#
#                 if tx.get('generated'):
#                     txtype = Transaction.MINING_REWARD
#
#                 # local comments have the highest priority
#                 if 'comment' in tx:
#                     comment = tx.get('comment')
#
#                 amount = tx['balance']['amount']
#                 balance += amount
#                 confirmations = tx['confirmations']
#
#                 tx_obj, created = Transaction.get_or_create(
#                     txid=txid, defaults=dict(
#                         datetime=dt,
#                         txtype=txtype,
#                         comment=comment,
#                         amount=amount,
#                         balance=balance,
#                         confirmations=confirmations
#                     )
#                 )
#                 if created:
#                     new_transactions.append(tx_obj)
#                 elif tx_obj.confirmations == 0 and confirmations != 0:
#                     tx_obj.confirmations = confirmations
#                     new_confirmations.append(tx_obj)
#                     tx_obj.save()
#
#     if len(new_transactions) > 0 or len(new_confirmations) > 0:
#         signals.listwallettransactions.emit(new_transactions, new_confirmations)
#     return len(new_transactions) != 0


def listpermissions():
    pass
    # client = get_active_rpc_client()
    # node_height = client.getblockcount()['result']
    #
    # perms = client.listpermissions()
    # if not perms:
    #     log.warning('no permissions from api')
    #     return
    # new_perms, new_votes = False, False
    #
    # Permission.delete().execute()
    # PendingVote.delete().execute()
    #
    # admin_addresses = set()
    # miner_addresses = set()
    #
    # with data_db.atomic():
    #     profile = Profile.get_active()
    #
    #     for perm in perms['result']:
    #         perm_type = perm['type']
    #         perm_start = perm['startblock']
    #         perm_end = perm['endblock']
    #
    #         if perm_type not in Permission.PERM_TYPES:
    #             continue
    #
    #         if perm_type == Permission.ADMIN and perm_start < node_height < perm_end:
    #             admin_addresses.add(perm['address'])
    #
    #         if perm_type == Permission.MINE and perm_start < node_height < perm_end:
    #             miner_addresses.add(perm['address'])
    #
    #         addr_obj, created = Address.get_or_create(address=perm['address'])
    #
    #         for vote in perm['pending']:
    #             # If candidate has already the permission continue.
    #             if vote['startblock'] == perm['startblock'] and vote['endblock'] == perm['endblock']:
    #                 continue
    #             start_block = vote['startblock']
    #             end_block = vote['endblock']
    #             # new stuff start
    #             for admin in vote['admins']:
    #                 admin_obj, created = Address.get_or_create(address=admin)
    #                 vote_obj, created = PendingVote.get_or_create(
    #                     address=addr_obj, perm_type=perm_type, start_block=start_block, end_block=end_block,
    #                     given_from=admin_obj
    #                 )
    #                 vote_obj.set_vote_type()
    #             # new stuff end
    #             approbations = len(vote['admins'])
    #             # TODO: Fix: current time of syncing is not the time of first_vote!
    #
    #         start_block = perm['startblock']
    #         end_block = perm['endblock']
    #         # TODO Why get_or_create ... we just deleted all Permission objects
    #         perm_obj, created = Permission.get_or_create(
    #             address=addr_obj, perm_type=perm_type, defaults=dict(start_block=start_block, end_block=end_block)
    #         )
    #         if created:
    #             new_perms = True
    #         else:
    #             perm_obj.save()
    #
    # new_is_admin = profile.address in admin_addresses
    # if profile.is_admin != new_is_admin:
    #     profile.is_admin = new_is_admin
    #
    # new_is_miner = profile.address in miner_addresses
    # if profile.is_miner != new_is_miner:
    #     profile.is_miner = new_is_miner
    #
    # if profile.dirty_fields:
    #     profile.save()
    #
    # # Todo: maybe only trigger table updates on actual change?
    # signals.listpermissions.emit()  # triggers community tab updates
    # signals.votes_changed.emit()  # triggers community tab updates
    # return {'new_perms': new_perms, 'new_votes': new_votes}




getblock_proccessed_height = 1


def getblock():
    """Process detailed data from individual blocks to find last votes from guardians"""
    pass
    # TODO cleanup this deeply nested mess :)

    # client = get_active_rpc_client()
    # global getblock_proccessed_height
    # blockchain_params = client.getblockchainparams()['result']
    # pubkeyhash_version = blockchain_params['address-pubkeyhash-version']
    # checksum_value = blockchain_params['address-checksum-value']
    #
    # block_objs = Block.multi_tx_blocks().where(Block.height > getblock_proccessed_height)
    #
    # votes_changed = False
    #
    # with data_db.atomic():
    #     for block_obj in block_objs:
    #         height = block_obj.height
    #         block_info = client.getblock("{}".format(height))['result']
    #         for txid in block_info['tx']:
    #             transaction = client.getrawtransaction(txid, 4)
    #             if transaction['error'] is None:
    #                 if 'vout' in transaction['result']:
    #                     vout = transaction['result']['vout']
    #                     permissions = []
    #                     start_block = None
    #                     end_block = None
    #                     for vout_key, entry in enumerate(vout):
    #                         if len(entry['permissions']) > 0:
    #                             for key, perm in entry['permissions'][0].items():
    #                                 if perm and key in permission_candidates:
    #                                     permissions.append(key)
    #                                 if key == 'startblock':
    #                                     start_block = perm
    #                                 if key == 'endblock':
    #                                     end_block = perm
    #                             in_entry = transaction['result']['vin'][vout_key]
    #                             public_key = in_entry['scriptSig']['asm'].split(' ')[1]
    #                             from_pubkey = public_key_to_address(public_key, pubkeyhash_version, checksum_value)
    #                             given_to = entry['scriptPubKey']['addresses']
    #                             for addr in given_to:
    #                                 log.debug(
    #                                     'Grant or Revoke {} given by {} to {} at time {}'.format(
    #                                         permissions, from_pubkey, addr, block_obj.time)
    #                                 )
    #                                 addr_from_obj, _ = Address.get_or_create(address=from_pubkey)
    #                                 addr_to_obj, _ = Address.get_or_create(address=addr)
    #                                 vote_obj, created = Vote.get_or_create(
    #                                     txid=txid, defaults=dict(
    #                                         from_address=addr_from_obj,
    #                                         to_address_id=addr_to_obj,
    #                                         time=block_obj.time
    #                                     )
    #                                 )
    #                                 if created:
    #                                     votes_changed = True
    #
    #         getblock_proccessed_height = height
    #
    # if votes_changed:
    #     signals.votes_changed.emit()



if __name__ == '__main__':
    import app
    app.init()
    process_permissions()
