# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from binascii import unhexlify
from datetime import datetime

import ubjson
from decimal import Decimal
from sqlalchemy import func

from app import enums
from app.tools.address import public_key_to_address
from app.responses import Getblockchaininfo
from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.helpers import batchwise
from app.models import Address, Permission, Transaction, PendingVote, data_db, Block, Profile, Alias, MiningReward,\
    WalletTransaction, Timestamp, Vote
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

    blockchain_params = client.getblockchainparams()['result']
    pubkeyhash_version = blockchain_params['address-pubkeyhash-version']
    checksum_value = blockchain_params['address-checksum-value']

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
            if process_transactions(block['height'], pubkeyhash_version, checksum_value):
                data_db().commit()
            else:
                data_db().rollback()
                return
    if last_valid_height != block_count_node:
        process_permissions()
        process_wallet_transactions()


def process_transactions(block_height, pubkeyhash_version, checksum_value):
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
            tx_relevant = process_inputs_and_outputs(tx["result"], pubkeyhash_version, checksum_value)

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


def process_inputs_and_outputs(raw_transaction, pubkeyhash_version, checksum_value) -> bool: #todo: better name
    relevant = False
    txid = raw_transaction["txid"]
    signers=[] #todo: SIGHASH_ALL
    my_address = Profile.get_active().address
    for n, vin in enumerate(raw_transaction["vin"]):
        # mining reward
        if 'coinbase' in vin:
            relevant = True
            mining_reward = raw_transaction["vout"][n]
            miner = mining_reward['scriptPubKey']['addresses'][0] #should be only one
            data_db().add(MiningReward(
                txid=txid,
                address=miner
            ))
            if miner == my_address:
                data_db().add(WalletTransaction(
                    txid = txid,
                    amount = mining_reward['value'],
                    tx_fee = 0,
                    comment = '',
                    tx_type = WalletTransaction.MINING_REWARD,
                    balance = None,
                ))
        elif 'scriptSig' in vin:
            public_key = vin['scriptSig']['asm'].split(' ')[1]
            signers.append(public_key_to_address(public_key, pubkeyhash_version, checksum_value))
    for vout in raw_transaction["vout"]:
        for item in vout["items"]:
            # stream item
            if item["type"] == "stream":
                publishers = item["publishers"]
                if publishers[0] == my_address:
                    data_db().add(WalletTransaction(
                        txid=txid,
                        amount=0,
                        tx_fee=vout['value'],
                        comment='Stream:"' + item['name'] + '", Key: "' + item['key'] + '"',
                        tx_type=WalletTransaction.PUBLISH,
                        balance=None
                    ))
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
        # vote
        for perm in vout['permissions']:
            relevant = True
            for perm_type, changed in perm.items():
                if changed and perm_type in permission_candidates:
                    for address in vout['scriptPubKey']['addresses']:
                        if address == my_address:
                            data_db().add(WalletTransaction(
                                txid=txid,
                                amount=0,
                                tx_fee=vout['value'],
                                comment='',
                                tx_type=WalletTransaction.VOTE,
                                balance=None
                            ))
                        Address.create_if_not_exists(address)
                        Address.create_if_not_exists(signers[vout['n']])
                        data_db().add(Vote(
                            txid=txid,
                            from_address=signers[vout['n']],
                            to_address=address,
                            start_block=perm['startblock'],
                            end_block=perm['endblock'],
                            perm_type=perm_type
                        ))
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
    signals.permissions_changed.emit()

def process_wallet_transactions():
    pass
    # client = get_active_rpc_client()
    # offset = 0
    # transactions_processed = False
    # actual_time_before = False
    # if data_db().query(WalletTransaction).count() > 0:
    #     actual_time_before = data_db().query(func.MAX(Block.time)).join(Transaction, WalletTransaction)
    # while(not transactions_processed):
    #     try:
    #         new_transactions = client.listwallettransactions(count = 100, skip=offset, verbose=False)['result']
    #     except Exception as e:
    #         log.debug(e)
    #         break
    #     if len(new_transactions) == 0:
    #         transactions_processed = True
    #     elif len(new_transactions) == 100:
    #         offset += 100
    #     for tx in new_transactions:
    #         txid = tx['txid']
    #         if WalletTransaction.wallet_transaction_in_db(txid):
    #             transactions_processed = True
    #             continue # or break??
    #         if tx['valid']:
    #             amount = tx['balance']['amount']
    #             transaction_types = []
    #
    #             # tx_type is vote
    #             if tx['permissions']:
    #                 transaction_types.append(WalletTransaction(
    #                     txid=txid,
    #                     amount=amount,
    #                     tx_fee=0,
    #                     comment='',
    #                     tx_type=WalletTransaction.VOTE,
    #                     balance=None
    #                 ))
    #
    #             # tx_type is publish
    #             for item in tx['items']:
    #                 if item['type'] == 'stream':
    #                     transaction_types.append(WalletTransaction(
    #                         txid=txid,
    #                         amount=amount,
    #                         tx_fee=0,
    #                         comment='Stream:"' + item['name'] + '", Key: "' + item['key'] + '"',
    #                         tx_type=WalletTransaction.PUBLISH,
    #                         balance=None
    #                     ))
    #                 else:
    #                     print(item) #todo: debug
    #
    #             # tx_type is mining reward
    #             if tx.get('generated'):
    #                 transaction_types.append(WalletTransaction(
    #                     txid=txid,
    #                     amount=amount,
    #                     tx_fee=0,
    #                     comment='',
    #                     tx_type=WalletTransaction.MINING_REWARD,
    #                     balance=None
    #                 ))
    #
    #             # tx_type is create
    #             if tx.get('create'):
    #                 transaction_types.append(WalletTransaction(
    #                     txid=txid,
    #                     amount=amount,
    #                     tx_fee=0,
    #                     comment='type: ' + tx['create']['type'] + ', name: ' + tx['create']['name'],
    #                     tx_type=WalletTransaction.CREATE,
    #                     balance=None
    #                 ))
    #
    #             if len(transaction_types) == 0:
    #                 transaction_types.append(WalletTransaction(
    #                     txid=txid,
    #                     amount=amount,
    #                     tx_fee=0,
    #                     comment = tx.get('comment') if tx.get('comment') else '',
    #                     tx_type=WalletTransaction.PAYMENT,
    #                     balance=None
    #                 ))
    #
    #             if not Transaction.transaction_in_db(txid):
    #                 data_db().add(Transaction(txid=txid, block=None, pos_in_block=0))
    #             if len(transaction_types) == 1:
    #                 #todo: tx_fee
    #                 data_db().add(transaction_types[0])
    #             else:
    #                 print(len(transaction_types)) #todo: split
    #     data_db().commit()

if __name__ == '__main__':
    import app
    app.init()
    process_wallet_transactions()
