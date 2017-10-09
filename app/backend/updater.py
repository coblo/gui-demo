# -*- coding: utf-8 -*-
"""Background Updater Thread"""
import time
from PyQt5 import QtCore
from app.backend.rpc import client

UNKNOWN_BALANCE = ' '
UNKNOWN_ADDRESS = ' '


class Updater(QtCore.QThread):

    balance_changed = QtCore.pyqtSignal(float)
    address_changed = QtCore.pyqtSignal(str)
    rpc_error = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_balance = UNKNOWN_BALANCE
        self.last_address = UNKNOWN_ADDRESS

    def __del__(self):
        self.wait()

    def run(self):
        while True:

            # Update Balance
            try:
                balance = client.getbalance()['result']
            except Exception as e:
                self.rpc_error.emit(str(e))
                balance = UNKNOWN_BALANCE
            if balance != self.last_balance:
                self.balance_changed.emit(balance)
                self.last_balance = balance

            # Update Address
            try:
                rtp = client.getruntimeparams()
                address = rtp['result']['handshakelocal']
            except Exception as e:
                self.rpc_error.emit(str(e))
                address = UNKNOWN_ADDRESS
            if address != self.last_address:
                self.address_changed.emit(address)
                self.last_address = address

            time.sleep(3)
