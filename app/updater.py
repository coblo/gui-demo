# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import time
import logging
from PyQt5 import QtCore
from app import sync
from app.backend.rpc import get_active_rpc_client


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

        while True:

            log.debug('check for new block or new local wallet updates')
            node_block_hash = self.client.getbestblockhash()['result']
            try:
                node_txid = self.client.listwallettransactions(1)['result'][0]['txid']
            except KeyError:
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

            self.sleep(self.UPDATE_INTERVALL)
