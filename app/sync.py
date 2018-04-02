# -*- coding: utf-8 -*-
"""Api to local database synchronization by api method"""
import logging
from binascii import unhexlify
from datetime import datetime

import ubjson
from decimal import Decimal
import app
from app import enums
from app.backend.rpc import get_active_rpc_client
from app.helpers import batchwise
from app.models import Address, Permission, Transaction, PendingVote, Block, Profile, Alias, MiningReward, \
    Timestamp, Vote
from app.models import ISCC
from app.models.db import profile_session_scope, data_session_scope
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
            info = client.getinfo()
            signals.getinfo.emit(info)
            new_balance = Decimal(str(info.balance))
            if new_balance != profile.balance:
                profile.balance = Decimal(info.balance)
        except Exception as e:
            log.debug(e)


def getblockchaininfo():
    """Emit headers and blocks (block sync status)"""
    client = get_active_rpc_client()
    try:
        info = client.getblockchaininfo()
        # Todo: Maybe track headers/blocks on Profile db model
        signals.getblockchaininfo.emit(info)
        return info
    except Exception as e:
        log.debug(e)
        return


def getruntimeparams():
    """Update wallet main address on current profile"""
    client = get_active_rpc_client()
    with profile_session_scope() as session:
        profile = Profile.get_active(session)
        params = client.getruntimeparams()

        if params.handshakelocal != profile.address:
            profile.address = params.handshakelocal


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
                block_from_chain = client.getblock('{}'.format(latest_block.height))
            except Exception as e:
                log.debug(e)
                return
            if latest_block.hash == unhexlify(block_from_chain['hash']):
                last_block_is_valid = True
                last_valid_height = latest_block.height
            else:
                session.delete(latest_block)

    blockchain_params = client.getblockchainparams()
    pubkeyhash_version = blockchain_params['address-pubkeyhash-version']
    checksum_value = blockchain_params['address-checksum-value']

    block_count_node = client.getblockcount()

    with data_session_scope() as session:
        # height is 0 indexed,
        for batch in batchwise(range(last_valid_height + 1, block_count_node), 100):
            try:
                with data_session_scope() as session:
                    new_blocks = client.listblocks(batch)

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
        block = client.getblock('{}'.format(block_height), 4)
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
        for item in vout.get("items", []):
            # stream item
            if item["type"] == "stream":
                publishers = item["publishers"]
                for publisher in publishers:
                    Address.create_if_not_exists(data_db, publisher)
                if item["name"] == app.STREAM_TIMESTAMP:
                    relevant = True
                    comment = ''
                    if item['data']:
                        data = ubjson.loadb(unhexlify(item['data']))
                        if 'comment' in data:
                            comment += data.get('comment', '')
                    data_db.add(Timestamp(
                        txid=txid,
                        pos_in_tx=i,
                        hash=item["keys"][0],
                        comment=comment,
                        address=publishers[0]
                    ))
                    # flush for the primary key
                    data_db.flush()
                elif item['name'] == app.STREAM_ALIAS:
                    alias = item["keys"][0]
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
                elif item['name'] == app.STREAM_ISCC:
                    iscc = item["keys"]
                    if len(iscc) != 4:
                        continue
                    meta_id, content_id, data_id, instance_id = iscc
                    if ISCC.already_exists(data_db, meta_id, content_id, data_id, instance_id):
                        continue
                    data = ubjson.loadb(unhexlify(item['data']))
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
        for perm in vout.get('permissions', []):
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


def process_permissions():
    # todo: check if we have new perms / votes
    client = get_active_rpc_client()

    try:
        perms = client.listpermissions("*", "*", True)
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
                    signals.votes_changed.emit()

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
