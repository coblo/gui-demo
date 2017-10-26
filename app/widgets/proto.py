from PyQt5 import QtWidgets

from PyQt5.QtGui import QIcon

import app
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
        self.check_box_exit_on_close.stateChanged['int'].connect(self.exit_on_close_changed)

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

    def closeEvent(self, event):
        if app.settings.value('exit_on_close', False, type=bool):
            QtWidgets.qApp.quit()
        else:
            event.ignore()
            self.hide()

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def exit_on_close_changed(self, state):
        app.settings.setValue('exit_on_close', state == 2)


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(MainWindow)

