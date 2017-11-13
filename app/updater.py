# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import logging
from PyQt5 import QtCore
from app import sync
from app.backend.rpc import get_active_rpc_client
from app.signals import signals


log = logging.getLogger(__name__)


class Updater(QtCore.QThread):

    UPDATE_INTERVALL = 3

    sync_funcs = (
        sync.getinfo,
        sync.getruntimeparams,
        sync.getblockchaininfo,
        sync.listblocks,
        sync.listwallettransactions,
        sync.listpermissions,
        sync.liststreamitems_alias,
        sync.getblock,
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug('init updater')

    def __del__(self):
        self.wait()

    @property
    def client(self):
        """Always use the rpc connection for the current profile"""
        return get_active_rpc_client()

    def run(self):

        synced_blockhash = ''
        synced_txid = ''
        blockchain_downloading = False

        while True:

            log.debug('check for new block or new local wallet updates')
            try:
                # This triggers Network Info widget update that we allways want
                blockchain_info = sync.getblockchaininfo()
                # The node is downloading blocks if it has more headers than blocks
                blockchain_downloading = blockchain_info['blocks'] != blockchain_info['headers']
                node_block_hash = blockchain_info['bestblockhash']
            except Exception as e:
                log.debug('cannot get bestblock via rpc: %s' % e)
                self.sleep(self.UPDATE_INTERVALL)
                continue

            if blockchain_downloading:
                log.debug('blockchain syncing - skip exspensive rpc calls')
                self.sleep(self.UPDATE_INTERVALL)
                continue

            try:
                node_txid = self.client.listwallettransactions(1)['result'][0]['txid']
            except (KeyError, IndexError):
                log.debug('no wallet transactions found')
                node_txid = ''

            if node_block_hash != synced_blockhash or node_txid != synced_txid:
                log.debug('starting full sync round')

                for sync_func in self.sync_funcs:
                    try:
                        log.debug('updating %s' % sync_func.__name__)
                        sync_func()
                    except Exception as e:
                        log.exception(e)

                synced_blockhash = node_block_hash
                synced_txid = node_txid
                signals.sync_cycle_finished.emit()

            self.sleep(self.UPDATE_INTERVALL)
