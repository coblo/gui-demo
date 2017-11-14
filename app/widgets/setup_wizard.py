# -*- coding: utf-8 -*-
import logging
import qrcode
import webbrowser
from PIL.ImageQt import ImageQt
from mnemonic import Mnemonic

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QTextCursor
from PyQt5 import QtWidgets
from os.path import exists

import app
from app.backend.rpc import RpcClient
from app.models import Profile, init_profile_db, init_data_db
from app.responses import Getblockchaininfo
from app.signals import signals
from app.tools.address import main_address_from_mnemonic, main_wif_from_mnemonic
from app.ui.setup_wizard import Ui_SetupWizard
from PyQt5.QtWidgets import QWizard, QLineEdit, QCheckBox, QApplication
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

    def __init__(self, parent=None, flags=Qt.WindowFlags(), **kwargs):
        super().__init__(parent, flags)

        self.updater = QApplication.instance().updater
        self.node = QApplication.instance().node

        self.setupUi(self)

        screen = QApplication.desktop().screenGeometry()
        self.move(screen.center() - self.rect().center())

        self.setPixmap(QWizard.LogoPixmap, QPixmap(':/images/resources/wizard_logo.png'))
        self.setPixmap(QWizard.BannerPixmap, QPixmap(':/images/resources/wizard_banner.png'))

        # Wizard state
        self._connection_tested = False
        self._blockchain_sync = False
        self._database_sync = False
        self._sync_ready = False
        self._mnemonic = None
        self._address = None
        self._manage_node = None

        # Global connections
        self.currentIdChanged.connect(self.current_id_changed)

        # Page 1 License agreement
        self.page1_license.isComplete = self.page1_license_is_complete
        self.radio_accept_license.clicked.connect(self.page1_license.completeChanged)
        self.radio_decline_icense.clicked.connect(self.page1_license.completeChanged)

        # Page 2 Choose Installation Mode
        self.button_group_choose_mode.buttonClicked.connect(self.next)

        # Page 3 Connect to existing node
        self.page3_connect.isComplete = self.page3_connect_is_complete
        self.page3_connect.cleanupPage = self.reset_connection_form
        self.button_test_connection.clicked.connect(self.test_connection)
        self.button_reset_connection_form.clicked.connect(self.reset_connection_form)

        # Page 4 Choose Account Create or Import
        self.page4_choose_account.initializePage = self.page4_choose_account_initialize_page
        self.page4_choose_account.cleanupPage = self.page4_choose_account_cleanup_page
        self.button_group_choose_account.buttonClicked.connect(self.next)

        # Page 5 Import Existing Account
        self.page5_import_account.isComplete = self.page5_import_account_is_complete
        self.page5_import_account.cleanupPage = self.page5_import_account_cleanup
        self.edit_seed.textChanged.connect(self.page5_import_account.completeChanged)

        # Page 6 Create Account
        self.button_generate_mnemonic.clicked.connect(self.generate_mnemonic)
        self.page6_create_account.isComplete = self.page6_create_account_is_complete
        self.page6_create_account.cleanupPage = self.page6_create_account_cleanup

        # Page 7 Initial Sync
        self.page7_sync.initializePage = self.page7_sync_initialize_page
        self.page7_sync.isComplete = self.page7_sync_is_complete
        self.button_get_coins.clicked.connect(lambda: webbrowser.open(app.GET_COINS_URL))
        signals.database_blocks_updated.connect(self.on_database_blocks_updated)
        signals.node_message.connect(self.on_node_message)
        signals.getblockchaininfo.connect(self.getblockchaininfo)
        signals.node_started.connect(self.on_node_started)

    @pyqtSlot(object)
    def getblockchaininfo(self, blockchaininfo: Getblockchaininfo):
        if self._blockchain_sync and blockchaininfo.headers > 10:
            self.progress_bar_initial_sync.setMaximum(blockchaininfo.headers)
            self.progress_bar_initial_sync.setValue(blockchaininfo.blocks)
            if blockchaininfo.headers == blockchaininfo.blocks:
                # Back to undefined progress
                self.progress_bar_initial_sync.setMaximum(0)
                self.progress_bar_initial_sync.setValue(0)
                self.log('Finished blockchain sync.')
                self._blockchain_sync = False
                self._database_sync = True

    @pyqtSlot(int, int)
    def on_database_blocks_updated(self, current_height, total_blocks):
        if self._database_sync:
            self.progress_bar_initial_sync.setMaximum(total_blocks)
            self.progress_bar_initial_sync.setValue(current_height)
            if current_height == total_blocks and current_height > 10:
                # Back to undefined progress
                self.progress_bar_initial_sync.setMaximum(0)
                self.progress_bar_initial_sync.setValue(0)
                self.log('Finished synching blocks to database.')
                self._sync_ready = True
                self.page7_sync.completeChanged.emit()

    @pyqtSlot(str)
    def on_node_message(self, msg):
        self.log(msg)

    @pyqtSlot()
    def on_node_started(self):
        self._blockchain_sync = True
        if not self.updater.isRunning():
            self.updater.start()

    @pyqtSlot(int)
    def current_id_changed(self, page_id: int):
        # Hide Next Button on Command Link Pages
        if page_id in (self.P2_CHOOSE_MODE, self.P4_CHOOSE_ACCOUNT):
            self.button(QWizard.NextButton).hide()
        if page_id == self.P7_SYNC:
            # Point of no return :)
            self.button(QWizard.BackButton).hide()

    @pyqtSlot()
    def generate_mnemonic(self):
        if self._mnemonic is None:
            self._mnemonic = Mnemonic('english').generate(256)
            self.label_new_seed_info.setText(
                'This is your mnemonic. Please make sure to create a safe backup of this phrase before you proceed!'
            )
            self.label_new_seed_info.setStyleSheet('color: red;')
            self.edit_new_seed.setPlainText(self._mnemonic)
            self.button_generate_mnemonic.hide()
            self.page6_create_account.completeChanged.emit()

    def page1_license_is_complete(self):
        return self.radio_accept_license.isChecked()

    def page3_connect_is_complete(self):
        # Verify connection to rpc host
        log.debug('Page 3 completion check request')
        return self._connection_tested

    def page4_choose_account_initialize_page(self):
        self._manage_node = True

    def page4_choose_account_cleanup_page(self):
        self._manage_node = False

    def page5_import_account_is_complete(self):
        words = self.edit_seed.toPlainText()

        if not words:
            self.edit_seed.setStyleSheet('background-color: white;')
            return False

        validator = Mnemonic('english')
        if validator.check(words):
            self.edit_seed.setStyleSheet('background-color: #c4df9b;')
            self._mnemonic = words
            return True
        else:
            self.edit_seed.setStyleSheet('background-color: #fff79a;')
            return False

    def page5_import_account_cleanup(self):
        self.edit_seed.setPlainText('')
        self.edit_seed.setStyleSheet('background-color: white;')
        self._mnemonic = None

    def page6_create_account_is_complete(self):
        return self._mnemonic is not None

    def page6_create_account_cleanup(self):
        self._mnemonic = None
        self.label_new_seed_info.setStyleSheet('color: black;')
        self.label_new_seed_info.setText(
            'You account is made from 24 words that are randomly generated. '
            'This is called a mnemonic. '
            'Click on "Create New Account" to generate your mnemonic!'
        )
        self.edit_new_seed.setPlainText('')
        self.button_generate_mnemonic.show()

    def page7_sync_initialize_page(self):
        if self._mnemonic and not self._address:
            self._address = main_address_from_mnemonic(self._mnemonic)

        self.label_address.setText(self._address)
        img = ImageQt(qrcode.make(self._address, box_size=3))
        self.label_qr_code.setPixmap(QPixmap.fromImage(img))

        if not exists(app.DATA_DIR):
            self.log('Creating data dir at: %s' % app.DATA_DIR)
            init_data_dir()

        self.log('Initialize profile database at: %s' % app.PROFILE_DB_FILEPATH)

        if self._manage_node:
            init_profile_db(create_default_profile=True)
        elif self._connection_tested:
            init_profile_db(create_default_profile=False)
            p_obj, created = Profile.get_or_create(
                name=self.edit_rpc_host.text(),
                defaults=dict(
                    rpc_host=self.edit_rpc_host.text(),
                    rpc_port=self.edit_rpc_port.text(),
                    rpc_user=self.edit_rpc_user.text(),
                    rpc_password=self.edit_rpc_password.text(),
                    rpc_use_ssl=self.cbox_use_ssl.isChecked(),
                    manage_node=False,
                    exit_on_close=True,
                    active=True,
                )
            )

        self.log('Initialize node-sync database')
        init_data_db()

        if self._manage_node:
            self.node.start(initprivkey=main_wif_from_mnemonic(self._mnemonic))
        else:
            self._database_sync = True
            if not self.updater.isRunning():
                self.updater.start()

    def page7_sync_is_complete(self):
        if self._sync_ready:
            self.button(QWizard.FinishButton).setStyleSheet('background-color: green;')
        return self._sync_ready

    def log(self, msg):
        self.edit_setup_log.moveCursor(QTextCursor.End)
        self.edit_setup_log.appendPlainText(msg)
        self.edit_setup_log.moveCursor(QTextCursor.End)

    @pyqtSlot()
    def test_connection(self):
        client = RpcClient(
            host=self.edit_rpc_host.text(),
            port=self.edit_rpc_port.text(),
            user=self.edit_rpc_user.text(),
            pwd=self.edit_rpc_password.text(),
            use_ssl=self.cbox_use_ssl.isChecked(),
        )
        try:
            response = client.getruntimeparams()
            assert response['error'] is None
        except Exception as e:
            log.exception(e)
            self.label_test_connection.setText('Connection error')
            return

        msg = 'Successfully connected to %s' % self.edit_rpc_host.text()
        self.label_test_connection.setText(msg)
        self.button_test_connection.setDisabled(True)
        self.gbox_connect.setEnabled(False)
        self._connection_tested = True
        self._address = response['result']['handshakelocal']
        self.page3_connect.completeChanged.emit()

    @pyqtSlot()
    def reset_connection_form(self):
        for wgt in self.gbox_connect.children():
            if isinstance(wgt, QLineEdit):
                wgt.clear()
            if isinstance(wgt, QCheckBox):
                wgt.setChecked(False)
        self.label_test_connection.setText('Please test the connection to proceed.')
        self.button_test_connection.setEnabled(True)
        self._connection_tested = False
        self._address = None
        self.gbox_connect.setEnabled(True)
        self.page3_connect.completeChanged.emit()

    def nextId(self):
        if self.currentId() == self.P2_CHOOSE_MODE:
            if self.button_connect_node.isChecked():
                return self.P3_CONNECT
            if self.button_setup_node.isChecked():
                return self.P4_CHOOSE_ACCOUNT
        if self.currentId() == self.P3_CONNECT:
            return self.P7_SYNC
        if self.currentId() == self.P4_CHOOSE_ACCOUNT:
            if self.button_account_create.isChecked():
                return self.P6_CREATE_ACCOUNT
            if self.button_account_import.isChecked():
                return self.P5_IMPORT_ACCOUNT
        if self.currentId() == self.P5_IMPORT_ACCOUNT:
            return self.P7_SYNC
        return super().nextId()


if __name__ == '__main__':
    import sys
    import traceback
    from PyQt5 import QtWidgets, Qt
    from app.helpers import init_logging, init_data_dir
    from app.updater import Updater
    from app.node import Node
    sys.excepthook = traceback.print_exception
    init_logging()
    wrapper = QtWidgets.QApplication(sys.argv)
    wrapper.setStyle('fusion')
    wizard = SetupWizard(node=Node(), updater=Updater())
    wizard.show()
    sys.exit(wrapper.exec())

