# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import time
from PyQt5 import QtCore
from app.backend.api import Api

UNKNOWN_BALANCE = ' '
UNKNOWN_ADDRESS = ' '


class Updater(QtCore.QThread):

    balance_changed = QtCore.pyqtSignal(float)
    address_changed = QtCore.pyqtSignal(str)
    api = Api()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_balance = UNKNOWN_BALANCE
        self.last_address = UNKNOWN_ADDRESS

    def __del__(self):
        self.wait()

    def run(self):
        while True:

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

            time.sleep(3)
