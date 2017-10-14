#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Application Main Window and Entry Point"""
import sys
import locale
import traceback
from PyQt5 import QtWidgets
from app.backend.api import Api
from app.backend.updater import Updater

from app.ui.main import Ui_MainWindow
from app.widgets.skills import WidgetSkills
from app.widgets.wallet_header import WalletHeader
from app.widgets.wallet_send import WalletSend
from app.widgets.wallet_history import WalletHistory
from app.widgets.community import Community
from app.widgets.create_privilege_request import CreatePrivilegeRequest


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.api = Api()

        self.updater = Updater()

        # Sidebar
        self.btn_group_nav.buttonClicked.connect(self.on_nav_change)
        self.widget_skills = WidgetSkills(self)
        self.layout_frame_sidebar.insertWidget(4, self.widget_skills)

        # Content
        self.stack_content.setCurrentIndex(0)
        self.layout_page_wallet.insertWidget(0, WalletHeader(self))
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


def main():
    app = QtWidgets.QApplication(sys.argv)
    locale.setlocale(locale.LC_ALL, '')
    window = MainWindow()

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    sys.excepthook = traceback.print_exception
    main()
