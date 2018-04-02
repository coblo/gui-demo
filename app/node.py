# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtCore import QProcess, QIODevice, QTextCodec
import app
from app.helpers import init_node_data_dir
from app.models import Profile
from app.signals import signals
from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)


class Node(QProcess):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = None
        self.started.connect(signals.node_started)
        self.started.connect(self.node_started)
        self.finished.connect(self.node_finished)
        self.finished.connect(signals.node_finished)
        self.errorOccurred.connect(self.node_error)
        self.errorOccurred.connect(signals.node_error)
        # self.setProcessChannelMode(QProcess.MergedChannels)
        self.readyReadStandardOutput.connect(self.on_stdout_ready)
        self.readyReadStandardError.connect(self.on_stderr_ready)
        self.decoder = QTextCodec.codecForLocale()
        self.reindex_required = False

    def start(self, *args, **kwargs):
        """Start node with active profile settings.

        :param str initprivkey: Optional WIF encoded private key for first time init.
        """

        initprivkey = kwargs.pop('initprivkey', None)

        try:
            self.profile = self.parent().profile
        except AttributeError:
            # In case of standalone usage
            from app.models.db import profile_session_scope
            with profile_session_scope() as session:
                self.profile = Profile.get_active(session)

        assert isinstance(self.profile, Profile)
        assert self.profile.manage_node, "active profile does not want to manage node"

        if self.state() == self.NotRunning:
            node_path = os.path.join(app.APP_DIR, 'app/bin/multichaind')
            if self.reindex_required:
                log.debug('starting node at: {} with -reindex=1'.format(node_path))
            else:
                log.debug('starting node at: {}'.format(node_path))

            # TODO only launch full bootstrap ip in first launch
            launch_args = [
                    app.NODE_BOOTSTRAP,
                    '-server=1',
                    # '-daemon',
                    '-autosubscribe=assets,streams',
                    '-autocombineminconf=4294967294',
                    # '-maxshowndata=32',
                    # '-printtoconsole',
                    '-reindex=' + ("1" if self.reindex_required else "0"),
                    # '-shortoutput',
                    '-rpcuser={}'.format(self.profile.rpc_user),
                    '-rpcpassword={}'.format(self.profile.rpc_password),
                    '-rpcbind={}'.format(self.profile.rpc_host),
                    '-rpcallowip={}'.format(self.profile.rpc_host),
                    '-rpcport={}'.format(self.profile.rpc_port),
                    '-datadir={}'.format(init_node_data_dir()),
                ]

            if initprivkey is not None:
                launch_args.append('-initprivkey={}'.format(initprivkey))

            super().start(node_path, launch_args, QIODevice.ReadOnly)
            self.reindex_required = False
        else:
            log.debug('node already started - state: {}'.format(self.state()))

    def stop(self):
        if self.state() == self.NotRunning:
            log.debug('node already stopped')
        else:
            return get_active_rpc_client().stop()

    def node_started(self):
        log.debug('node started')

    def node_finished(self, code, status):
        if code == self.CrashExit:
            self.start()
        log.debug('node finished code {} status {}'.format(code, status))

    def node_error(self, error):
        log.debug('node error: {}'.format(error))

    def on_stdout_ready(self):
        if self.canReadLine():
            data = self.readAllStandardOutput()
            text = self.decoder.toUnicode(data).strip()
            if text:
                signals.node_message.emit(text)

    def on_stderr_ready(self):
        data = self.readAllStandardError()
        text = self.decoder.toUnicode(data).strip()
        if text:
            # check if the node needs a reindex to recover
            # multichaind doesn't seem to use error codes
            if "Please restart multichaind with reindex=1" in text:
                self.reindex_required = True
                signals.node_message.emit(text)
