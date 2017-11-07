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
        while True:

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

            for sync_func in sync_funcs:
                try:
                    log.debug('updating %s' % sync_func.__name__)
                    sync_func()
                except Exception as e:
                    log.exception(e)

            time.sleep(self.UPDATE_INTERVALL)
