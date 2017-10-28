# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtCore import QProcess
import app
from app.helpers import init_node_data_dir
from app.models import Profile
from app.signals import signals
from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)


class Node(QProcess):

    def __init__(self, parent):
        super().__init__(parent)
        self.profile = Profile.get_active()
        assert isinstance(self.profile, Profile)
        assert self.profile.manage_node, "profile does not want to manage node"
        self.started.connect(signals.node_started)
        self.started.connect(self.node_started)
        self.finished.connect(self.node_finished)
        self.finished.connect(signals.node_finished)
        self.errorOccurred.connect(self.node_error)
        self.errorOccurred.connect(signals.node_error)

    def start(self, *args, **kwargs):
        if self.state() == self.NotRunning:
            node_path = os.path.join(app.APP_DIR, 'app/bin/multichaind')
            log.debug('starting node at: {}'.format(node_path))
            super().start(
                node_path, [
                    app.NODE_BOOTSTRAP,
                    '-server=1',
                    '-daemon',
                    '-autosubscribe=assets,streams',
                    '-maxshowndata=32',
                    '-rpcuser={}'.format(self.profile.rpc_user),
                    '-rpcpassword={}'.format(self.profile.rpc_password),
                    '-rpcbind={}'.format(self.profile.rpc_host),
                    '-rpcallowip={}'.format(self.profile.rpc_host),
                    '-rpcport={}'.format(self.profile.rpc_port),
                    '-datadir={}'.format(init_node_data_dir()),
                ]
            )
        else:
            log.debug('node already started - state: {}'.format(self.state()))

    def stop(self):
        if self.state() == self.NotRunning:
            log.debug('node already stopped')
        else:
            try:
                get_active_rpc_client().stop()
            except Exception as e:
                log.debug('cannot reach node to stop {}'.format(e))

    def node_started(self):
        log.debug('node started')

    def node_finished(self, code, status):
        log.debug('node finished code {} status {}'.format(code, status))

    def node_error(self, error):
        log.debug('node error: {}'.format(error))
