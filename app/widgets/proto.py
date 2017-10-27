from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from app.backend.updater import Updater
from app.models import Profile
from app import helpers
from app.node import Node
from app.signals import signals
from app.ui.proto import Ui_MainWindow
import app


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Basic initialization
        self.data_dir = helpers.init_data_dir()
        self.profile_db = helpers.init_profile_db()
        self.profile = Profile.get_active()
        self.node_data_dir = helpers.init_node_data_dir()

        # Init Navigation
        self.btn_grp_nav.setId(self.btn_nav_wallet, 0)
        self.btn_grp_nav.setId(self.btn_nav_community, 1)
        self.btn_grp_nav.setId(self.btn_nav_settings, 2)
        self.btn_nav_wallet.setChecked(True)
        self.wgt_content.setCurrentIndex(0)

        # Settings
        self.check_box_exit_on_close.setChecked(self.profile.exit_on_close)
        self.check_box_exit_on_close.stateChanged['int'].connect(self.setting_changed_exit_on_close)
        self.check_manage_node.setChecked(self.profile.manage_node)
        self.check_manage_node.stateChanged['int'].connect(self.setting_changed_manage_node)

        # Init TrayIcon
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

        # Progress bar
        self.progress_bar_network_info.setMinimum(0)
        signals.block_sync_changed.connect(self.on_block_sync_changed)
        signals.node_started.connect(self.node_started)

        # Backend processes
        self.node = Node(self)
        self.updater = Updater(self)

        if self.profile.manage_node:
            self.node.start()

        self.tray_icon.show()
        self.show()
        self.statusbar.showMessage(app.APP_DIR, 10000)

    def closeEvent(self, event):
        if self.profile.exit_on_close:
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

    def on_block_sync_changed(self, data):
        self.progress_bar_network_info.setMaximum(data.get('headers'))
        self.progress_bar_network_info.setValue(data.get('blocks'))


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(MainWindow)

