import logging
from PyQt5 import QtWidgets
from decimal import Decimal, ROUND_DOWN

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import app
from app import helpers
from app import models
from app.models import Profile, Permission, VotingRound
from app.node import Node
from app.responses import Getblockchaininfo
from app.signals import signals
from app.ui.proto import Ui_MainWindow
from app.updater import Updater
from app.widgets.community_tables import CommunityTableView
from app.widgets.wallet_history import WalletHistory
from app.widgets.wallet_send import WalletSend


log = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setupUi(self)

        # Basic initialization
        self.data_dir = helpers.init_data_dir()
        self.profile_db = models.init_profile_db()
        self.node_data_dir = helpers.init_node_data_dir()
        self.data_db = models.init_data_db()
        self.profile = None
        log.debug('load current profile: %s' % self.profile)
        self.load_profile()
        signals.profile_changed.connect(self.load_profile)

        # Init Navigation
        self.btn_grp_nav.setId(self.btn_nav_wallet, 0)
        self.btn_grp_nav.setId(self.btn_nav_community, 1)
        self.btn_grp_nav.setId(self.btn_nav_settings, 2)
        self.btn_nav_wallet.setChecked(True)
        self.wgt_content.setCurrentIndex(0)

        # Patch custom widgets
        self.gbox_wallet_transactions.setParent(None)
        self.gbox_wallet_send.setParent(None)

        wallet_send = WalletSend(self)
        self.lout_page_wallet_v.addWidget(wallet_send)

        wallet_history = WalletHistory(self)
        self.lout_page_wallet_v.addWidget(wallet_history)

        self.table_validators.setParent(None)
        table_validators = CommunityTableView(self, perm_type=Permission.MINE)
        self.tab_validators.layout().insertWidget(0, table_validators)

        self.table_guardians.setParent(None)
        table_guardians = CommunityTableView(self, perm_type=Permission.ADMIN)
        self.tab_guardians.layout().insertWidget(0, table_guardians)

        # Settings
        self.check_box_exit_on_close.setChecked(self.profile.exit_on_close)
        self.check_box_exit_on_close.stateChanged['int'].connect(self.setting_changed_exit_on_close)
        self.check_manage_node.setChecked(self.profile.manage_node)
        self.check_manage_node.stateChanged['int'].connect(self.setting_changed_manage_node)

        # Init TrayIcon
        # Todo: fix issue of multiple tray icons poping up
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':images/resources/app_icon.png'))
        self.tray_icon.activated.connect(self.on_tray_activated)

        show_action = QtWidgets.QAction("Show", self)
        quit_action = QtWidgets.QAction("Exit", self)
        hide_action = QtWidgets.QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QtWidgets.qApp.quit)

        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        # Connections
        signals.getblockchaininfo.connect(self.getblockchaininfo)
        signals.listpermissions.connect(self.listpermissions)
        signals.node_started.connect(self.node_started)

        # Backend processes
        self.updater = Updater(self)

        if self.profile.manage_node:
            # Todo check for existing node process
            self.node = Node(self)
            self.node.start()
        else:
            # No managed node to wait for... start updater
            self.updater.start()

        self.tray_icon.show()
        self.show()
        self.statusbar.showMessage(app.APP_DIR, 10000)

    @pyqtSlot()
    def load_profile(self):
        """Read current active profile and set gui labels"""
        self.profile = Profile.get_active()

        self.lbl_wallet_alias.setText(self.profile.alias)
        self.lbl_wallet_address.setText(self.profile.address)

        normalized = self.profile.balance.quantize(Decimal('.01'), rounding=ROUND_DOWN)
        display = "{0:n} {1}".format(normalized, app.CURRENCY_CODE)
        self.lbl_wallet_balance.setText(display)
        self.lbl_wallet_balance.setToolTip("{0:n} {1}".format(
            self.profile.balance, app.CURRENCY_CODE)
        )

    def format_balance(self, balance):
        display = "{0:n}".format(balance.normalize()) if balance is not ' ' else balance
        return display + ' CHM'

    def closeEvent(self, event):
        if self.profile.exit_on_close:
            if hasattr(self, 'node'):
                self.node.kill()
            self.profile_db.close()
            QtWidgets.qApp.quit()
        else:
            event.ignore()
            self.hide()

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def setting_changed_exit_on_close(self, state):
        self.profile.exit_on_close = state == 2
        self.profile.save()

    def setting_changed_manage_node(self, state):
        self.profile.manage_node = state == 2
        self.profile.save()
        if self.profile.manage_node:
            self.node.start()

    def node_started(self):
        self.updater.start()

    @pyqtSlot(object)
    def getblockchaininfo(self, blockchaininfo: Getblockchaininfo):
        self.progress_bar_network_info.setMaximum(blockchaininfo.headers)
        self.progress_bar_network_info.setValue(blockchaininfo.blocks)
        self.label_network_info.setText(blockchaininfo.description)

    @pyqtSlot()
    def listpermissions(self):
        num_validators = Permission.num_validators()
        log.debug('set num validators %s' % num_validators)
        self.lbl_num_validators.setText(str(num_validators))

        num_guardians = Permission.num_guardians()
        log.debug('set num guardians %s' % num_guardians)
        self.lbl_num_guardians.setText(str(num_guardians))

        num_candidates = VotingRound.num_candidates()
        log.debug('set num candidates %s' % num_candidates)
        self.lbl_num_candidates.setText(str(num_candidates))


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(MainWindow)

