from PyQt5 import QtWidgets

from app.tools.runner import run_widget
from app.ui.proto import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_grp_nav.setId(self.btn_nav_wallet, 0)
        self.btn_grp_nav.setId(self.btn_nav_community, 1)
        self.btn_grp_nav.setId(self.btn_nav_settings, 2)
        self.btn_nav_wallet.setChecked(True)
        self.wgt_content.setCurrentIndex(0)


if __name__ == '__main__':
    run_widget(MainWindow)
