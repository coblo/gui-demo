from PyQt5.QtWidgets import QWidget
from app.ui.wallet_send import Ui_widget_wallet_send


class WalletSend(QWidget, Ui_widget_wallet_send):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)