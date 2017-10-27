# -*- coding: utf-8 -*-
"""QT Signals that the application provides"""
from PyQt5.QtCore import QObject, pyqtSignal, QProcess


class Signals(QObject):

    # Blockchain node status
    node_started = pyqtSignal()
    node_finished = pyqtSignal(int, QProcess.ExitStatus)
    node_error = pyqtSignal(QProcess.ProcessError)

    # Blockchain sync
    block_sync_changed = pyqtSignal(dict)


signals = Signals()
