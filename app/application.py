import locale
import logging
import sys
import traceback

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import app
from app import helpers
from app.models import init_profile_db, init_data_db
from app.node import Node
from app.signals import signals
from app.updater import Updater
from app.widgets.proto import MainWindow
from app.widgets.setup_wizard import SetupWizard

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
        try:
            log.debug('user locale is {}'.format(locale.getlocale(locale.LC_ALL)))
        except TypeError as e:
            log.debug(repr(e))

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
        font_db.addApplicationFont(':/fonts/resources/RobotoCondensed-Light.ttf')
        font_db.addApplicationFont(':/fonts/resources/RobotoMono-Light.ttf')
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
        helpers.init_data_dir()
        signals.application_start.connect(self.on_application_start)

    def on_application_start(self):
        init_profile_db()
        self.updater = Updater(self)
        self.node = Node(self)
        self.aboutToQuit.connect(self.cleanup)

        from app.models.db import profile_session_scope
        with profile_session_scope() as session:
            is_first_start = app.is_first_start(session)

        if is_first_start:
            wizard = SetupWizard()
            if wizard.exec() == SetupWizard.Rejected:
                QtWidgets.qApp.quit()
                return
        else:
            init_data_db()

        # Initialize main window
        self.ui = self.main_widget()

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
                log.debug('attempt graceful node shuttdown via rpc')
                rpc_result = self.node.stop()
                log.debug('rpc stop returned: %s' % rpc_result)
            except Exception as e:
                log.exception('failed rpc shutdown - try to kill node process')
                self.node.kill()

        if self.tray_icon is not None:
            self.tray_icon.deleteLater()

        log.debug('finished app teardown cleanup - quitting.')

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.ui.show()
            self.ui.activateWindow()
