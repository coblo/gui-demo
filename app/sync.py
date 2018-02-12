# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from binascii import unhexlify
from datetime import datetime

import ubjson

from app import enums
from app.backend.rpc import get_active_rpc_client
from app.helpers import batchwise
from app.models import Address, Permission, Transaction, PendingVote, Block, Profile, Alias, MiningReward, \
    WalletTransaction, Timestamp, Vote
from app.models import ISCC
from app.models.db import profile_session_scope, data_session_scope
from app.responses import Getblockchaininfo
from app.signals import signals
from app.tools.address import public_key_to_address
from app.tools.validators import is_valid_username

log = logging.getLogger(__name__)

permission_candidates = ['admin', 'mine', 'issue', 'create']


def getinfo():
    """Update latest wallet balance on current profile"""
    client = get_active_rpc_client()
    with profile_session_scope() as session:
        profile = Profile.get_active(session)
        try:
            result = client.getinfo()['result']
            if result['balance'] != profile.balance:
                profile.balance = result['balance']
        except Exception as e:
            log.debug(e)


def getblockchaininfo():
    """Emit headers and blocks (block sync status)"""
    client = get_active_rpc_client()
    try:
        result = client.getblockchaininfo()['result']
        # Todo: Maybe track headers/blocks on Profile db model
        signals.getblockchaininfo.emit(Getblockchaininfo(**result))
        return result
    except Exception as e:
        log.debug(e)
        return


def getruntimeparams():
    """Update wallet main address on current profile"""
    client = get_active_rpc_client()
    with profile_session_scope() as session:
        profile = Profile.get_active(session)
        result = client.getruntimeparams()['result']

        if result['handshakelocal'] != profile.address:
            profile.address = result['handshakelocal']


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
    with data_session_scope() as session:
        while not last_block_is_valid:
            latest_block = session.query(Block).order_by(Block.height.desc()).first()
            if not latest_block:
                break
            try:
                block_from_chain = client.getblock(hash_or_height='{}'.format(latest_block.height))['result']
            except Exception as e:
                log.debug(e)
                return
            if latest_block.hash == unhexlify(block_from_chain['hash']):
                last_block_is_valid = True
                last_valid_height = latest_block.height
            else:
                session.delete(latest_block)

    blockchain_params = client.getblockchainparams()['result']
    pubkeyhash_version = blockchain_params['address-pubkeyhash-version']
    checksum_value = blockchain_params['address-checksum-value']

    block_count_node = client.getblockcount()['result']

    with data_session_scope() as session:
        Transaction.delete_unconfirmed(session)

        # height is 0 indexed,
        for batch in batchwise(range(last_valid_height + 1, block_count_node), 100):
            try:
                with data_session_scope() as session:
                    answer = client.listblocks(batch)
                    if answer['error'] is None:
                        new_blocks = answer['result']
                    else:
                        log.debug(answer['error'])
                        return

                    for block in new_blocks:
                        block_obj = Block(
                            hash=unhexlify(block['hash']),
                            height=block['height'],
                            mining_time=datetime.fromtimestamp(block['time']),
                        )
                        session.add(block_obj)
                        session.add(MiningReward(
                            block=unhexlify(block['hash']),
                            address=block['miner']
                        ))
                        Address.create_if_not_exists(session, block['miner'])
                        if block['txcount'] > 1:
                            process_transactions(session, block['height'], pubkeyhash_version, checksum_value)
                        signals.database_blocks_updated.emit(block['height'], block_count_node)
                        signals.blockschanged.emit(session.query(Block).count())
            except Exception as e:
                log.debug(e)
                return

    if last_valid_height != block_count_node:
        # permissions and votes tables are completely refreshed after each new block
        process_permissions()


def process_transactions(data_db, block_height, pubkeyhash_version, checksum_value):
    client = get_active_rpc_client()

    try:
        block = client.getblock(hash_or_height='{}'.format(block_height), verbose=4)['result']
    except Exception as e:
        log.debug(e)
        return

    for pos_in_block, tx in enumerate(block['tx']):
        try:
            tx_relevant = process_inputs_and_outputs(data_db, tx, pubkeyhash_version, checksum_value)

        except Exception as e:
            log.debug(e)
            return

        # add only relevant TXs to the database.
        if tx_relevant:
            Transaction.create_if_not_exists(
                data_db,
                Transaction(
                    txid=tx['txid'],
                    pos_in_block=pos_in_block,
                    block=unhexlify(block['hash'])
                )
            )


def process_inputs_and_outputs(data_db, raw_transaction, pubkeyhash_version,
                               checksum_value) -> bool:  # todo: better name
    relevant = False
    txid = raw_transaction["txid"]
    signers = []  # todo: SIGHASH_ALL
    for n, vin in enumerate(raw_transaction["vin"]):
        if 'scriptSig' in vin:
            public_key = vin['scriptSig']['asm'].split(' ')[1]
            signers.append(public_key_to_address(public_key, pubkeyhash_version, checksum_value))
    for i, vout in enumerate(raw_transaction["vout"]):
        for item in vout["items"]:
            # stream item
            if item["type"] == "stream":
                publishers = item["publishers"]
                for publisher in publishers:
                    Address.create_if_not_exists(data_db, publisher)
                if item["name"] == "timestamp":
                    relevant = True
                    comment = ''
                    for entry in raw_transaction['data']:
                        data = ubjson.loadb(unhexlify(entry))
                        if 'comment' in data:
                            comment += data.get('comment', '')
                    data_db.add(Timestamp(
                        txid=txid,
                        pos_in_tx=i,
                        hash=item["key"],
                        comment=comment,
                        address=publishers[0]
                    ))
                    # flush for the primary key
                    data_db.flush()
                elif item['name'] == "alias":
                    alias = item["key"]
                    # Sanity checks
                    if item["data"] or not is_valid_username(alias) or len(publishers) != 1:
                        continue
                    relevant = True
                    data_db.add(Alias(
                        txid=txid,
                        pos_in_tx=i,
                        address=publishers[0],
                        alias=alias
                    ))
                    # flush for the primary key
                    data_db.flush()
                elif item['name'] == "testiscc":
                    iscc = item["key"].split('-')
                    if len(iscc) != 4:
                        continue
                    meta_id, content_id, data_id, instance_id = iscc
                    if ISCC.already_exists(data_db, meta_id, content_id, data_id, instance_id):
                        continue
                    data = ubjson.loadb(unhexlify(raw_transaction['data'][0]))
                    if 'title' not in data:
                        continue
                    relevant = True
                    data_db.add(ISCC(
                        txid=txid,
                        address=publishers[0],
                        meta_id=meta_id,
                        content_id=content_id,
                        data_id=data_id,
                        instance_id=instance_id,
                        title=data['title']
                    ))
                    # flush for the primary key
                    data_db.flush()
        # vote
        for perm in vout['permissions']:
            relevant = True
            for perm_type, changed in perm.items():
                if changed and perm_type in permission_candidates:
                    for address in vout['scriptPubKey']['addresses']:
                        Address.create_if_not_exists(data_db, address)
                        Address.create_if_not_exists(data_db, signers[vout['n']])
                        data_db.add(Vote(
                            txid=txid,
                            pos_in_tx=i,
                            from_address=signers[vout['n']],
                            to_address=address,
                            start_block=perm['startblock'],
                            end_block=perm['endblock'],
                            perm_type=perm_type
                        ))
                        # flush for the primary key
                        data_db.flush()
    return relevant


def process_wallet_txs():
    client = get_active_rpc_client()
    i = 0
    finished = False
    has_new_transactions = False
    has_new_confirmed_transactions = False
    try:
        wallet_addresses = client.getaddresses(False)["result"]
    except Exception as e:
        log.debug(e)
        return
    with data_session_scope() as session:
        while not finished:
            wallet_txs = client.listwallettransactions(count=10, skip=i, verbose=True)
            i += 10
            if wallet_txs['error'] is not None:
                log.debug(wallet_txs['error'])
                break

            if len(wallet_txs['result']) == 0:
                break

            for wallet_tx in reversed(wallet_txs['result']):
                if WalletTransaction.wallet_transaction_in_db(session, wallet_tx['txid']):
                    finished = True
                    break

                if wallet_tx.get('valid') is False:
                    continue

                has_new_transactions = True
                has_new_confirmed_transactions = False
                amount = wallet_tx['balance']['amount']
                is_payment = True
                if wallet_tx.get('generated'):
                    if session.query(MiningReward.address).join(Block).filter(Block.hash == unhexlify(
                            wallet_tx["blockhash"])).first().address not in wallet_addresses:
                        log.debug("wallet transaction is invalid")
                        continue
                    session.add(WalletTransaction(
                        txid=wallet_tx['txid'],
                        amount=amount,
                        comment='',
                        tx_type=WalletTransaction.MINING_REWARD,
                        balance=None
                    ))
                    # flush for primary key
                    session.flush()
                    amount = 0
                    is_payment = False
                for item in wallet_tx['items']:
                    session.add(WalletTransaction(
                        txid=wallet_tx['txid'],
                        amount=amount,
                        comment='Stream:"' + item['name'] + '", Key: "' + item['key'] + '"',
                        tx_type=WalletTransaction.PUBLISH,
                        balance=None
                    ))
                    # flush for primary key
                    session.flush()
                    amount = 0
                    is_payment = False
                for perm in wallet_tx['permissions']:
                    session.add(WalletTransaction(
                        txid=wallet_tx['txid'],
                        amount=amount,
                        comment='',
                        tx_type=WalletTransaction.VOTE,
                        balance=None
                    ))
                    # flush for primary key
                    session.flush()
                    amount = 0
                    is_payment = False
                if wallet_tx.get('create'):
                    session.add(WalletTransaction(
                        txid=wallet_tx['txid'],
                        amount=amount,
                        comment='Type:"' + wallet_tx['create']['type'] + '", Name: "' + wallet_tx['create'][
                            'name'] + '"',
                        tx_type=WalletTransaction.CREATE,
                        balance=None
                    ))
                    # flush for primary key
                    session.flush()
                    amount = 0
                    is_payment = False
                if is_payment:
                    comment = wallet_tx.get('comment')
                    session.add(WalletTransaction(
                        txid=wallet_tx['txid'],
                        amount=amount,
                        comment='' if comment is None else comment,
                        tx_type=WalletTransaction.PAYMENT,
                        balance=None
                    ))
                    # flush for primary key
                    session.flush()
                # check if we already have the block
                if wallet_tx.get('blockhash') and Block.block_exists(session, wallet_tx.get('blockhash')):
                    has_new_confirmed_transactions = True
                    # if the block is already in our database we can create the transaction with as a "confirmed" one
                    Transaction.create_if_not_exists(
                        session,
                        Transaction(
                            txid=wallet_tx['txid'],
                            pos_in_block=wallet_tx.get('blockindex', 0),
                            block=unhexlify(wallet_tx.get('blockhash'))
                        )
                    )
                else:
                    # create as unconfirmed, if the block isn't in our database yet even if the transaction is confirmed
                    Transaction.create_if_not_exists(
                        session,
                        Transaction(
                            txid=wallet_tx['txid'],
                            pos_in_block=wallet_tx.get('blockindex', 0),
                            block=None
                        )
                    )

    if has_new_transactions:
        if has_new_confirmed_transactions:
            with data_session_scope() as session:
                WalletTransaction.compute_balances(session)
        signals.wallet_transactions_changed.emit()


def process_permissions():
    # todo: check if we have new perms / votes
    client = get_active_rpc_client()

    try:
        perms = client.listpermissions()['result']
    except Exception as e:
        log.debug(e)
        return

    with data_session_scope() as session:
        session.query(Permission).delete()
        session.query(PendingVote).delete()

    with data_session_scope() as session:
        for perm in perms:
            perm_type = perm['type']
            perm_start = perm['startblock']
            perm_end = perm['endblock']
            address = perm['address']

            Address.create_if_not_exists(session, address)

            if perm_type not in [enums.ISSUE, enums.CREATE, enums.MINE, enums.ADMIN]:
                continue

            perm_obj = Permission(
                address=address,
                perm_type=perm_type,
                start_block=perm_start,
                end_block=perm_end
            )
            session.add(perm_obj)

            for vote in perm['pending']:
                start_block = vote['startblock']
                end_block = vote['endblock']
                # If candidate has already the permission continue.
                if start_block == perm['startblock'] and end_block == perm['endblock']:
                    continue
                for admin in vote['admins']:
                    Address.create_if_not_exists(session, admin)
                    vote_obj = PendingVote(
                        address_from=admin,
                        address_to=address,
                        perm_type=perm_type,
                        start_block=start_block,
                        end_block=end_block
                    )
                    session.add(vote_obj)

    with profile_session_scope() as profile_db:
        profile = Profile.get_active(profile_db)

        with data_session_scope() as data_db:
            is_admin, is_miner = Permission.get_permissions_for_address(data_db, profile.address)
            if is_admin != profile.is_admin:
                profile.is_admin = is_admin
                signals.is_admin_changed.emit(is_admin)
            if is_miner != profile.is_miner:
                profile.is_miner = is_miner
                signals.is_miner_changed.emit(is_miner)

    signals.permissions_changed.emit()


if __name__ == '__main__':
    import app

    app.init()
    with data_session_scope() as session:
        WalletTransaction.compute_balances(session)
