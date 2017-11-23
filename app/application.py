import sys
import traceback
import locale
import logging

import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox

import app
from app import helpers
from app.models import Profile
from app.node import Node
from app.updater import Updater
from app.widgets.proto import MainWindow
from app.widgets.setup_wizard import SetupWizard
from app.signals import signals

from app.backend.rpc import get_active_rpc_client

helpers.init_logging()
log = logging.getLogger(__name__)


class Application(QtWidgets.QApplication):
    def __init__(self, args, main_widget=None):
        log.debug('init app')
        super().__init__(args)

        if not app.is_frozen():
            sys.excepthook = traceback.print_exception

        self.setQuitOnLastWindowClosed(False)

        # Initialize application metadata
        locale.setlocale(locale.LC_ALL, '')
        self.setOrganizationName(app.ORG_NAME)
        self.setOrganizationDomain(app.ORG_DOMAIN)
        self.setApplicationDisplayName(app.APP_NAME)
        self.setApplicationName(app.APP_NAME)
        self.setApplicationVersion(app.APP_VERSION)

        # Gui Styles and Fonts
        self.setStyle('fusion')
        font_db = QtGui.QFontDatabase()
        font_db.addApplicationFont(':/fonts/resources/Roboto-Light.ttf')
        font_db.addApplicationFont(':/fonts/resources/RobotoCondensed-Regular.ttf')
        font_db.addApplicationFont(':/fonts/resources/Oswald-Regular.ttf')
        font_db.addApplicationFont(':/fonts/resources/Oswald-SemiBold.ttf')
        app_font = QtGui.QFont("Roboto Light")
        app_font.setStyleStrategy(QtGui.QFont.PreferAntialias | QtGui.QFont.PreferQuality)
        app_font.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.setFont(app_font)

        # Instantiate workers
        self.updater = None
        self.node = None

        self.main_widget = main_widget if main_widget else MainWindow

        self.ui = None
        self.tray_icon = None
        signals.application_start.connect(self.on_application_start)

    def on_application_start(self):
        self.updater = Updater(self)
        self.node = Node(self)
        self.aboutToQuit.connect(self.cleanup)
        signals.profile_changed.connect(self.on_profile_changed)

        if app.is_first_start():
            wizard = SetupWizard()
            if wizard.exec() == SetupWizard.Rejected:
                QtWidgets.qApp.quit()
                return

        # Initialize main window
        self.ui = self.main_widget()

        if self.account_balance_zero():
            self.ui.setDisabled(True)
            profile = Profile.get_active()
            QMessageBox.information(QMessageBox(), "Account Balance is 0",
                                    "To use this application you will need \"Charm\", the currency we use on our Blockchain.<br>"
                                    "You can get \"Charm\" <a href='https://t.me/ContentBlockchainBeta'>here</a>.<br>"
                                    "Your address is {}.".format(profile.address))

        # Init TrayIcon
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':images/resources/app_icon.png'))
        self.tray_icon.activated.connect(self.on_tray_activated)

        show_action = QtWidgets.QAction("Show", self)
        quit_action = QtWidgets.QAction("Exit", self)
        hide_action = QtWidgets.QAction("Hide", self)
        show_action.triggered.connect(self.ui.show)
        hide_action.triggered.connect(self.ui.hide)
        quit_action.triggered.connect(QtWidgets.qApp.quit)

        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Shortcuts
        if hasattr(self.ui, 'node'):
            self.ui.debug_shortcut = QtWidgets.QShortcut('Ctrl+K', self.ui, self.node.kill)
            self.ui.debug_shortcut = QtWidgets.QShortcut('Ctrl+S', self.ui, self.node.stop)
            self.ui.debug_shortcut = QtWidgets.QShortcut('Ctrl+R', self.ui, self.node.start)

    @pyqtSlot()
    def cleanup(self):
        """Final application teardown/cleanup"""
        log.debug('init app teardown cleanup')

        if self.node is not None:
            try:
                log.debug('attempt gracefull node shuttdown via rpc')
                rpc_result = self.node.stop()
                log.debug('rpc stop returned: %s' % rpc_result)
            except Exception as e:
                log.exception('failed rpc shutdown - try to kill node process')
                self.node.kill()

        if self.ui is not None:
            self.ui.data_db.close()
            self.ui.profile_db.close()

        if self.tray_icon is not None:
            self.tray_icon.deleteLater()

        log.debug('finished app teardown cleanup - quitting.')

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.ui.show()
            self.ui.activateWindow()

    def account_balance_zero(self):
        if Profile.get_active().balance == 0:
            # We only make a rpc-call, if we see in the profile, that the user has no coins
            client = get_active_rpc_client()
            if client.getbalance()['result'] == 0:
                return True

    def on_profile_changed(self, new_profile):
        try:
            self.ui.setDisabled(new_profile.balance == 0)
        except Exception as e:
            log.debug(e)
