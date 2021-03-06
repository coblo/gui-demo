import logging
import webbrowser

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

import app
from app import enums
from app import helpers
from app.models import Profile, Permission, PendingVote
from app.models.db import profile_session_scope, data_session_scope
from app.responses import Getblockchaininfo, Getinfo
from app.signals import signals
from app.ui.proto import Ui_MainWindow
from app.widgets.apply import ApplyDialog
from app.widgets.candidates import CandidateTableView
from app.widgets.change_alias import ChangeAlias
from app.widgets.community_tables import CommunityTableView
from app.widgets.invite import InviteDialog
from app.widgets.iscc import WidgetISCC
from app.widgets.timestamp import WidgetTimestamping
from app.widgets.token import WidgetToken
from app.widgets.wallet_history import WalletHistory
from app.widgets.wallet_send import WalletSend

log = logging.getLogger(__name__)

TRANSACTION_INFORMATION = 'transaction information'
BALANCE_INFORMATION = 'balance information'


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Instantiate workers
        self.updater = QApplication.instance().updater
        self.node = QApplication.instance().node

        self.data_dir = helpers.init_data_dir()
        self.node_data_dir = helpers.init_node_data_dir()
        with profile_session_scope() as session:
            self.profile = Profile.get_active(session)

        # Setup Widgets
        self.setupUi(self)

        # Hide information widget
        font = QFont('Roboto Light', 10)
        self.label_info_text.setFont(font)
        self.btn_close_info.setFont(font)
        font.setUnderline(True)
        self.btn_info_action.setFont(font)
        self.widget_information.setHidden(True)
        self.btn_close_info.clicked.connect(self.hide_information)
        signals.new_unconfirmed.connect(self.show_transaction_info)
        self.information_type = None

        self.on_profile_changed(self.profile)
        signals.profile_changed.connect(self.on_profile_changed)

        self.permissions_changed()
        signals.permissions_changed.connect(self.permissions_changed)

        # Init Navigation
        self.btn_grp_nav.setId(self.btn_nav_wallet, 0)
        self.btn_grp_nav.setId(self.btn_nav_iscc, 1)
        self.btn_grp_nav.setId(self.btn_nav_timestamp, 2)
        self.btn_grp_nav.setId(self.btn_nav_token, 3)
        self.btn_grp_nav.setId(self.btn_nav_community, 4)
        self.btn_grp_nav.setId(self.btn_nav_settings, 5)
        self.btn_nav_wallet.setChecked(True)
        self.wgt_content.setCurrentIndex(0)

        # Patch custom widgets
        self.tab_widget_cummunity.setStyleSheet('QPushButton {padding: 5 12 5 12; font: 10pt "Roboto Light"}')

        self.gbox_wallet_transactions.setParent(None)
        self.gbox_wallet_send.setParent(None)

        wallet_send = WalletSend(self)
        self.lout_page_wallet_v.addWidget(wallet_send)

        wallet_history = WalletHistory(self)
        self.lout_page_wallet_v.addWidget(wallet_history)

        widget_iscc = WidgetISCC(self)
        self.lout_page_iscc_v.addWidget(widget_iscc)

        widget_timestamp = WidgetTimestamping(self)
        self.lout_page_timestamp_v.addWidget(widget_timestamp)

        widget_token = WidgetToken(self)
        self.lout_page_token_v.addWidget(widget_token)

        self.table_validators.setParent(None)
        table_validators = CommunityTableView(self, perm_type=enums.MINE)
        self.tab_validators.layout().insertWidget(0, table_validators)

        self.table_guardians.setParent(None)
        table_guardians = CommunityTableView(self, perm_type=enums.ADMIN)
        self.tab_guardians.layout().insertWidget(0, table_guardians)

        self.table_candidates.setParent(None)
        table_candidates = CandidateTableView(self)
        self.tab_candidates.layout().insertWidget(0, table_candidates)

        # Statusbar
        self.label_statusbar = QtWidgets.QLabel('')
        self.statusbar.addPermanentWidget(self.label_statusbar)

        # Dialog Button hookups
        invite_dialog = InviteDialog(self)
        self.button_invite_canditate.clicked.connect(invite_dialog.exec)
        apply_dialog = ApplyDialog(self)
        self.button_apply_guardian.clicked.connect(apply_dialog.exec)
        self.button_apply_validator.clicked.connect(apply_dialog.exec)

        # Settings
        self.check_box_exit_on_close.setChecked(self.profile.exit_on_close)
        self.check_box_exit_on_close.stateChanged['int'].connect(self.setting_changed_exit_on_close)
        self.check_manage_node.setChecked(self.profile.manage_node)
        self.check_manage_node.stateChanged['int'].connect(self.setting_changed_manage_node)
        self.btn_alias_change.clicked.connect(self.on_change_alias)

        # Connections
        signals.getinfo.connect(self.getinfo)
        signals.getblockchaininfo.connect(self.getblockchaininfo)
        signals.node_started.connect(self.node_started)
        signals.rpc_error.connect(self.rpc_error)
        signals.blockschanged.connect(self.getdatabaseinfo)
        signals.on_balance_status_changed.connect(self.on_balance_status_changed)
        with data_session_scope() as session:
            from app.models import Block
            self.progress_bar_database_info.setValue(session.query(Block).count())

        if self.profile.manage_node:
            # Todo check for existing node process
            self.node.start()
        else:
            # No managed node to wait for... start updater
            self.updater.start()

        self.show()

    @pyqtSlot(Profile)
    def on_profile_changed(self, new_profile):
        """Read current active profile and set gui labels"""
        self.profile = new_profile
        log.debug('load current profile %s' % self.profile)

        self.lbl_alias.setText(new_profile.alias)

        self.lbl_skill_is_admin.setEnabled(self.profile.is_admin)
        self.lbl_skill_is_miner.setEnabled(self.profile.is_miner)
        # We must manually "polish" the style to trigger visuals
        self.lbl_skill_is_admin.style().polish(self.lbl_skill_is_admin)
        self.lbl_skill_is_miner.style().polish(self.lbl_skill_is_miner)

        if any((self.profile.is_admin, self.profile.is_miner)):
            self.gbox_community_skills.show()
        else:
            self.gbox_community_skills.hide()

        self.button_apply_validator.setVisible(not self.profile.is_miner)
        self.button_apply_guardian.setVisible(not self.profile.is_admin)
        self.button_invite_canditate.setVisible(self.profile.is_admin)

        if self.profile.balance <= 0:
            self.balance_is_0()
            signals.on_balance_status_changed.emit(True)
        else:
            signals.on_balance_status_changed.emit(False)
            if self.information_type == BALANCE_INFORMATION:
                self.hide_information()

    def on_balance_status_changed(self, balance_is_zero):
        self.btn_alias_change.setDisabled(balance_is_zero)
        self.button_invite_canditate.setDisabled(balance_is_zero)
        if balance_is_zero:
            self.btn_alias_change.setToolTip('You need coins to change your alias.')
            self.button_invite_canditate.setToolTip('You need coins to invite a candidate.')

    def closeEvent(self, event):
        if self.profile.exit_on_close:
            QtWidgets.qApp.quit()
        else:
            event.ignore()
            self.hide()

    def setting_changed_exit_on_close(self, state):
        self.profile.exit_on_close = state == 2
        with profile_session_scope() as session:
            session.add(self.profile)

    def setting_changed_manage_node(self, state):
        self.profile.manage_node = state == 2
        with profile_session_scope() as session:
            session.add(self.profile)

        if self.profile.manage_node:
            self.node.start()

    def node_started(self):
        self.updater.start()

    def on_change_alias(self):
        dialog = ChangeAlias(self)
        dialog.show()
        return dialog

    def change_to_wallet(self):
        self.wgt_content.setCurrentIndex(0)

    def balance_is_0(self):
        if self.information_type is None:
            self.show_balance_info()
        elif self.information_type == TRANSACTION_INFORMATION:
            QTimer().singleShot(6000, self.show_balance_info)

    def show_transaction_info(self, type):
        self.widget_information.setHidden(False)
        self.btn_info_action.setHidden(self.wgt_content.currentIndex() == 0)
        self.btn_info_action.setText("See transaction log for confirmation.")
        self.btn_info_action.clicked.connect(self.change_to_wallet)
        self.label_info_text.setText('Your {} has been submitted to the blockchain.'.format(type))
        self.widget_information.setStyleSheet("border-radius: 6%; background: #16BBEF; color: #fff; padding: 5px, 2px, 5px, 2px;")
        self.information_type = TRANSACTION_INFORMATION
        QTimer().singleShot(5000, self.hide_information)

    def hide_information(self):
        self.widget_information.setHidden(True)
        self.btn_info_action.clicked.disconnect()
        self.information_type = None

    def show_balance_info(self):
        self.widget_information.setHidden(False)
        self.btn_info_action.setHidden(False)
        self.btn_info_action.setText("Get some coins here.")
        self.btn_info_action.clicked.connect(lambda: webbrowser.open(app.GET_COINS_URL))
        self.label_info_text.setText("You have no coins. Every transaction needs coins.")
        self.widget_information.setStyleSheet("border-radius: 6%; background: #FF8D00; color: #fff; padding: 5px, 2px, 5px, 2px;")
        self.information_type = BALANCE_INFORMATION

    @pyqtSlot(object)
    def getinfo(self, info: Getinfo):
        tpl = "Gui: v{} | Net: {} | Node: v{} | Protocol: v{} | Relayfee: {} | Connections: {}"
        netinfo = tpl.format(
            app.APP_VERSION, info.description, info.version, info.protocolversion,
            float(info.relayfee), info.connections,
        )
        self.label_statusbar.setText(netinfo)

    @pyqtSlot(object)
    def getblockchaininfo(self, blockchaininfo: Getblockchaininfo):
        self.progress_bar_network_info.setMaximum(blockchaininfo.headers + 1)
        self.progress_bar_database_info.setMaximum(blockchaininfo.headers + 1)
        self.progress_bar_network_info.setValue(blockchaininfo.blocks + 1)

    @pyqtSlot(str)
    def rpc_error(self, msg: str):
        self.statusbar.showMessage(msg, 1000 * 5)

    @pyqtSlot(object)
    def getdatabaseinfo(self, databaseinfo):
        self.progress_bar_database_info.setValue(databaseinfo)


    @pyqtSlot()
    def permissions_changed(self):
        with data_session_scope() as session:
            num_validators = Permission.num_validators(session)
            self.lbl_num_validators.setText(str(num_validators))

            num_guardians = Permission.num_guardians(session)
            self.lbl_num_guardians.setText(str(num_guardians))

            num_candidates = PendingVote.num_candidates(session)
            self.lbl_num_candidates.setText(str(num_candidates))


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(MainWindow)

