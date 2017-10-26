# -*- coding: utf-8 -*-
import logging

import os
from PyQt5.QtCore import QProcess
import app
from app.backend.rpc import client
from app.signals import signals

log = logging.getLogger(__name__)


class Node(QProcess):

    def __init__(self, parent):
        super().__init__(parent)

        self.started.connect(signals.node_started)
        self.started.connect(self.node_started)
        self.finished.connect(self.node_finished)
        self.finished.connect(signals.node_finished)
        self.errorOccurred.connect(self.node_error)
        self.errorOccurred.connect(signals.node_error)

    def start(self, *args, **kwargs):
        if self.state() == self.NotRunning:
            node_path = os.path.join(app.APP_DIR, 'bin/multichaind')
            log.debug('starting node')
            super().start(
                node_path, [
                    app.NODE_BOOTSTRAP,
                    '-server=1',
                    '-daemon',
                    '-rpcuser={}'.format(app.NODE_RPC_USER),
                    '-rpcpassword={}'.format(app.NODE_RPC_PASSWORD),
                    '-rpcbind={}'.format(app.NODE_RPC_HOST),
                    '-rpcallowip={}'.format(app.NODE_RPC_HOST),
                    '-rpcport={}'.format(app.NODE_RPC_PORT),
                    '-datadir={}'.format(app.DATA_DIR),
                ]
            )
        else:
            log.debug('node already started - state: {}'.format(self.state()))

    def stop(self):
        if self.state() == self.NotRunning:
            log.debug('node already stopped')
        else:
            try:
                client.stop()
            except Exception:
                log.debug('cannot reach node to stop')

    def node_started(self):
        log.debug('node started')

    def node_finished(self, code, status):
        log.debug('node finished code {} status {}'.format(code, status))

    def node_error(self, error):
        log.debug('node error: {}'.format(error))
