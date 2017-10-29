# -*- coding: utf-8 -*-
"""QT Signals that the application provides"""
from PyQt5.QtCore import QObject, pyqtSignal, QProcess


class Signals(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sync')

    # Blockchain node status
    node_started = pyqtSignal()
    node_finished = pyqtSignal(int, QProcess.ExitStatus)
    node_error = pyqtSignal(QProcess.ProcessError)

    # rpc method syncs
    getinfo = pyqtSignal(object)
    getblockchaininfo = pyqtSignal(object)
    getruntimeparams = pyqtSignal(object)

    listwallettransactions = pyqtSignal()

    block_sync_changed = pyqtSignal(dict)
    transactions_changed = pyqtSignal(list)


signals = Signals()
