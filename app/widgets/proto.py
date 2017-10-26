from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

import app
from app.backend.updater import Updater
from app.node import Node
from app.signals import signals
from app.ui.proto import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Init Navigation
        self.btn_grp_nav.setId(self.btn_nav_wallet, 0)
        self.btn_grp_nav.setId(self.btn_nav_community, 1)
        self.btn_grp_nav.setId(self.btn_nav_settings, 2)
        self.btn_nav_wallet.setChecked(True)
        self.wgt_content.setCurrentIndex(0)

        # Settings
        self.check_box_exit_on_close.setChecked(app.settings.value('exit_on_close', False, type=bool))
        self.check_box_exit_on_close.stateChanged['int'].connect(self.setting_changed_exit_on_close)
        self.check_manage_node.setChecked(app.settings.value('manage_node', True, type=bool))
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

        self.tray_icon.show()

        # Progress bar
        self.progress_bar_network_info.setMinimum(0)
        signals.block_sync_changed.connect(self.on_block_sync_changed)

        signals.node_started.connect(self.node_started)

        # Backend processes
        self.node = Node(self)
        self.updater = Updater(self)

        if app.settings.value('manage_node', True, type=bool):
            self.node.start()

    def closeEvent(self, event):
        if app.settings.value('exit_on_close', False, type=bool):
            self.node.kill()
            QtWidgets.qApp.quit()
        else:
            event.ignore()
            self.hide()

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def setting_changed_exit_on_close(self, state):
        app.settings.setValue('exit_on_close', state == 2)

    def setting_changed_manage_node(self, state):
        app.settings.setValue('manage_node', state == 2)
        self.node.start()

    def node_started(self):
        self.updater.start()

    def on_block_sync_changed(self, data):
        self.progress_bar_network_info.setMaximum(data.get('headers'))
        self.progress_bar_network_info.setValue(data.get('blocks'))


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(MainWindow)

