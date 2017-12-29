# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import logging

from PyQt5 import QtCore

from app import sync
from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.models import Alias
from app.models import Profile
from app.models.db import profile_session_scope, data_session_scope

log = logging.getLogger(__name__)


class Updater(QtCore.QThread):

    UPDATE_INTERVALL = 3

    sync_funcs = (
        sync.getinfo,
        sync.getruntimeparams,
        sync.getblockchaininfo,
        sync.process_blocks,
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug('init updater')
    #
    # def __del__(self):
    #     self.wait()

    @property
    def client(self):
        """Always use the rpc connection for the current profile"""
        return get_active_rpc_client()

    def run(self):

        synced_blockhash = ''
        blockchain_downloading = False

        with profile_session_scope() as profile_session:
            profile = Profile.get_active(profile_session)
            with data_session_scope() as data_session:
                profile.alias = Alias.get_alias_by_address(data_session, profile.address)

        while True:

            log.debug('check for new block or new local wallet updates')
            try:
                # This triggers Network Info widget update that we always want
                blockchain_info = sync.getblockchaininfo()
                # The node is downloading blocks if it has more headers than blocks
                blockchain_downloading = blockchain_info['blocks'] != blockchain_info['headers']
                node_block_hash = blockchain_info['bestblockhash']
            except Exception as e:
                log.exception('cannot get bestblock via rpc: %s' % e)
                self.sleep(self.UPDATE_INTERVALL)
                continue

            if blockchain_downloading:
                log.debug('blockchain syncing - skip expensive rpc calls')
                self.sleep(self.UPDATE_INTERVALL)
                continue

            if node_block_hash != synced_blockhash:
                log.debug('starting full sync round')

                for sync_func in self.sync_funcs:
                    try:
                        log.debug('updating %s' % sync_func.__name__)
                        sync_func()
                    except Exception as e:
                        log.exception(e)

                synced_blockhash = node_block_hash
                signals.sync_cycle_finished.emit()

            # update the unconfirmed transactions
            try:
                sync.process_wallet_txs()
            except Exception as e:
                log.exception(e)
            except (KeyError, IndexError):
                log.debug('no wallet transactions found')

            self.sleep(self.UPDATE_INTERVALL)
