from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QWidget

from app.tools.validators import AddressValidator
from app.ui.wallet_send import Ui_widget_wallet_send


class WalletSend(QWidget, Ui_widget_wallet_send):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.edit_address.setValidator(AddressValidator())

        self.edit_address.textChanged.connect(self.check_state)
        self.edit_address.textChanged.emit(self.edit_address.text())

    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QValidator.Acceptable:
            color = '#c4df9b'  # green
        elif state == QValidator.Intermediate:
            color = '#fff79a'  # yellow
        else:
            color = '#f6989d'  # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

