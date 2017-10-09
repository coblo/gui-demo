from PyQt5.QtWidgets import QWidget
from app.ui.wallet_history import Ui_widget_wallet_history


class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)