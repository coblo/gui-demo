# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import time
import logging
from PyQt5 import QtCore
from app.signals import signals
from app import responses
from app import sync
from app.backend.rpc import get_active_rpc_client
from app.enums import Method


log = logging.getLogger(__name__)


class Updater(QtCore.QThread):

    UPDATE_INTERVALL = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug('init updater')
        # Init autosync properties
        for method in Method:
            if method.autosync:
                setattr(self, method.name, None)

    def __del__(self):
        self.wait()

    @property
    def client(self):
        """Always use the rpc connection for the current profile"""
        return get_active_rpc_client()

    def update_api_method(self, methodname):
        """Update by rpc api method name (only for simple flat api methods)"""
        result = getattr(self.client, methodname)()['result']
        result_obj = getattr(responses, methodname.title())(**result)
        if result_obj != getattr(self, methodname):
            setattr(self, methodname, result_obj)
            getattr(signals, methodname).emit(result_obj)

    def run(self):
        while True:

            # Update all autosync api methods
            for method in Method:
                if method.autosync:
                    try:
                        log.debug('updating %s' % method.name)
                        self.update_api_method(method.name)
                    except Exception as e:
                        log.exception(e)

            # Database syncs
            sync_funcs = (
                sync.listblocks,
                sync.listwallettransactions,
                sync.listpermissions,
                sync.liststreamitems_alias,
            )

            for sync_func in sync_funcs:
                try:
                    log.debug('updating %s' % sync_func.__name__)
                    num_items_updated = sync_func()
                    if num_items_updated:
                        signal = getattr(signals, sync_func.__name__)
                        signal.emit()
                except Exception as e:
                    log.exception(e)

            time.sleep(self.UPDATE_INTERVALL)

    def update_permissions(self):
        perms = self.api.get_skills()
        if perms != self.last_permissions:
            self.permissions_changed.emit(perms)
            self.last_permissions = perms

    def update_transaction(self):
        transactions = self.api.get_transactions()
        if transactions != self.last_transactions:
            self.transactions_changed.emit(transactions)
            self.last_transactions = transactions

    def update_addresses(self):
        addresses = self.api.get_addresses()
        if addresses != self.last_addresses:
            self.addresses_changed.emit(addresses)
            self.last_addresses = addresses

    # def update_chainstatus(self):
    #     chain_info = self.client.getblockchaininfo()['result']
    #     if chain_info:
    #         signals.block_sync_changed.emit(chain_info)

    # def on_send(self):
    #     self.update_addresses()
    #     self.update_transaction()
