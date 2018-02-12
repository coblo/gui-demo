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

    # simple rpc method syncs
    getinfo = pyqtSignal(object)
    getblockchaininfo = pyqtSignal(object)
    getruntimeparams = pyqtSignal(object)

    # database rpc syncs
    wallet_transactions_changed = pyqtSignal()
    permissions_changed = pyqtSignal()
    liststreamitems_alias = pyqtSignal()
    listblocks = pyqtSignal()
    blockschanged = pyqtSignal(object)

    application_start = pyqtSignal()

    votes_changed = pyqtSignal()

    # custom signals

    #: profile changed
    profile_changed = pyqtSignal(object)

    iscc_inserted = pyqtSignal()

    # wallettransactions changed
    wallet_transaction_inserted = pyqtSignal(object)
    wallet_transaction_updated = pyqtSignal(object)
    new_unconfirmed = pyqtSignal(str)

    block_sync_changed = pyqtSignal(dict)
    transactions_changed = pyqtSignal(list)

    is_admin_changed = pyqtSignal(bool)
    is_miner_changed = pyqtSignal(bool)

    # emitted when the sync for new blocks was finished
    sync_cycle_finished = pyqtSignal()

    # Emmitted by sync.listblocks to report node -> db sync
    # Emmits synched_block_height, node_block_height ints
    database_blocks_updated = pyqtSignal(int, int)

    # Signals standard output from managed node process
    node_message = pyqtSignal(str)



signals = Signals()
