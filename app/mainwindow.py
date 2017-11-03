#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Application Main Window and Entry Point"""
from PyQt5 import QtWidgets

from app.backend.api import Api
from app.ui.main import Ui_MainWindow
from app.updater import Updater
from app.widgets.community import Community
from app.widgets.create_privilege_request import CreatePrivilegeRequest
from app.widgets.skills import WidgetSkills
from app.widgets.wallet_addresses import WalletAddresses
from app.widgets.wallet_header import WalletHeader
from app.widgets.wallet_history import WalletHistory
from app.widgets.wallet_send import WalletSend


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.api = Api()

        self.updater = Updater()
        self.updater.chainstatus_changed.connect(self.on_chainstatus_changed)

        # Sidebar
        self.btn_group_nav.buttonClicked.connect(self.on_nav_change)
        self.widget_skills = WidgetSkills(self)
        self.layout_frame_sidebar.insertWidget(4, self.widget_skills)

        # Content
        self.stack_content.setCurrentIndex(0)
        self.layout_page_wallet.insertWidget(0, WalletHeader(self))
        self.layout_wallet_addresses.addWidget(WalletAddresses(self))
        self.layout_wallet_send.addWidget(WalletSend(self))
        self.layout_wallet_history.addWidget(WalletHistory(self))
        self.layout_community.addWidget(Community(self))
        self.layout_privilege_request.addWidget(CreatePrivilegeRequest(self, self.change_stack_index))

        self.updater.start()

    def on_nav_change(self, btn):
        name = btn.objectName()
        if name == 'btn_nav_wallet':
            self.change_stack_index(0)
        if name == 'btn_nav_community':
            self.change_stack_index(1)

    def change_stack_index(self, new_index):
        self.stack_content.setCurrentIndex(new_index)

    def on_chainstatus_changed(self, data):
        percentage = (data.get('blocks') / data.get('headers')) * 100
        self.progbar_blockchain_sync.setValue(int(percentage))
        msg = 'Synced {} blocks of {}'.format(data.get('blocks'), data.get('headers'))
        self.statusbar.showMessage(msg, 10000)
