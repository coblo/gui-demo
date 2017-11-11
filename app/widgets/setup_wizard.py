# -*- coding: utf-8 -*-
import logging

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPixmap
from app.ui.setup_wizard import Ui_SetupWizard
from PyQt5.QtWidgets import QWizard
from app.ui import resources_rc

log = logging.getLogger(__name__)


class SetupWizard(QWizard, Ui_SetupWizard):

    P1_LICENSE = 0
    P2_CHOOSE_MODE = 1
    P3_CONNECT = 2
    P4_CHOOSE_ACCOUNT = 3
    P5_IMPORT_ACCOUNT = 4
    P6_CREATE_ACCOUNT = 5
    P7_SYNC = 6

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setPixmap(QWizard.LogoPixmap, QPixmap(':/images/resources/wizard_logo.png'))
        self.setPixmap(QWizard.BannerPixmap, QPixmap(':/images/resources/wizard_banner.png'))

        # Global connections
        self.currentIdChanged.connect(self.current_id_changed)

        # Page 1 License agreement
        self.page1_license.isComplete = self.page1_license_is_complete
        self.radio_accept_license.clicked.connect(self.page1_license.completeChanged)
        self.radio_decline_icense.clicked.connect(self.page1_license.completeChanged)

        # Page 2 Choose Installation Mode
        self.button_group_choose_mode.buttonClicked.connect(self.next)

        # Page 3 Choose Account Create or Import
        self.button_group_choose_account.buttonClicked.connect(self.next)


    @pyqtSlot(int)
    def current_id_changed(self, page_id: int):
        # Hide Next Button on Command Link Pages
        if page_id in (self.P2_CHOOSE_MODE, self.P4_CHOOSE_ACCOUNT):
            self.button(QWizard.NextButton).hide()

    @pyqtSlot()
    def page1_license_is_complete(self):
        return self.radio_accept_license.isChecked()

    def page2_next_id(self):
        log.debug('PAGE NEXT ID CALLED')
        selection = self.button_group_choose_mode.checkedId()
        log.debug('Selected button %s' % selection)
        if self.button_connect_node.isChecked():
            return self.P3_CONNECT
        elif self.button_setup_node.isChecked():
            return self.P4_CHOOSE_ACCOUNT

    def nextId(self):
        if self.currentId() == self.P2_CHOOSE_MODE:
            if self.button_connect_node.isChecked():
                return self.P3_CONNECT
            if self.button_setup_node.isChecked():
                return self.P4_CHOOSE_ACCOUNT
        if self.currentId() == self.P4_CHOOSE_ACCOUNT:
            if self.button_account_create.isChecked():
                return self.P6_CREATE_ACCOUNT
            if self.button_account_import.isChecked():
                return self.P5_IMPORT_ACCOUNT
        return super().nextId()


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    from app.helpers import init_logging
    # import app
    # app.init()
    init_logging()
    wrapper = QtWidgets.QApplication(sys.argv)
    wrapper.setStyle('fusion')
    wizard = SetupWizard()
    wizard.show()
    sys.exit(wrapper.exec())

