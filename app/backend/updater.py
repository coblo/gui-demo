# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import time
import logging
from PyQt5 import QtCore

from decimal import Decimal

from app.backend.api import Api
from app.backend.rpc import client

UNKNOWN_BALANCE = ' '
UNKNOWN_ADDRESS = ' '

log = logging.getLogger(__name__)

class Updater(QtCore.QThread):

    UPDATE_INTERVALL = 3

    chainstatus_changed = QtCore.pyqtSignal(dict)
    balance_changed = QtCore.pyqtSignal(Decimal)
    address_changed = QtCore.pyqtSignal(str)
    permissions_changed = QtCore.pyqtSignal(list)
    transactions_changed = QtCore.pyqtSignal(list)
    addresses_changed = QtCore.pyqtSignal(list)

    api = Api()

    def __init__(self, parent=None):
        log.debug('init updater')

        super().__init__(parent)
        self.last_changestatus = {}
        self.last_balance = UNKNOWN_BALANCE
        self.last_address = UNKNOWN_ADDRESS
        self.last_permissions = []
        self.last_transactions = []
        self.last_addresses = []

    def __del__(self):
        self.wait()

    def run(self):
        while True:

            # Update Chainstatus
            self.update_chainstatus()

            # Update Balance
            balance = self.api.get_balance()
            if balance is None:
                balance = UNKNOWN_BALANCE
            if balance != self.last_balance:
                self.balance_changed.emit(balance)
                self.last_balance = balance

            # Update Address
            address = self.api.get_main_address()
            if address is None:
                address = UNKNOWN_ADDRESS
            if address != self.last_address:
                self.address_changed.emit(address)
                self.last_address = address

            self.update_permissions()
            self.update_addresses()
            self.update_transaction()

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

    def update_chainstatus(self):
        chain_info = client.getblockchaininfo()['result']
        if chain_info:
            self.chainstatus_changed.emit(chain_info)

    def on_send(self):
        self.update_addresses()
        self.update_transaction()


