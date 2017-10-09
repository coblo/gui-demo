import sys
import traceback
from PyQt5 import QtWidgets, QtGui, QtCore
from app.resources import resources_rc


class NavButton(QtWidgets.QPushButton):

    def __init__(self, *args, **kwargs):
        super(NavButton, self).__init__(*args, **kwargs)
        self.setCheckable(True)
        self.setMinimumHeight(50)


class SidebarNav(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(SidebarNav, self).__init__(parent)

        # Wallet Button
        self.btn_wallet = NavButton('Wallet', self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/money_white.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap(":/images/money_black.svg"), QtGui.QIcon.Active, QtGui.QIcon.Off)
        self.btn_wallet.setIcon(icon)
        self.btn_wallet.setIconSize(QtCore.QSize(24, 24))
        self.btn_wallet.setChecked(True)

        # Community Button
        self.btn_community = NavButton('Community', self)
        self.btn_settings = NavButton('Settings', self)

        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)

        self.layout_main.addWidget(self.btn_wallet)
        self.layout_main.addWidget(self.btn_community)
        self.layout_main.addWidget(self.btn_settings)
        self.setLayout(self.layout_main)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.button_group.addButton(self.btn_wallet)
        self.button_group.addButton(self.btn_community)
        self.button_group.addButton(self.btn_settings)
        self.button_group.setExclusive(True)

        self.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                color: white;
                background-color: black;
                text-align: left;
                padding: 0 20 0 20;
            }
            
            QPushButton:checked {
                color: black;
                background-color: white;
            }
        """)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SidebarNav()
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
