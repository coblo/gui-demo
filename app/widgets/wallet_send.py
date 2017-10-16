from PyQt5.QtGui import QValidator, QDoubleValidator
from PyQt5.QtWidgets import QWidget

from app import settings
from app.tools.validators import AddressValidator
from app.ui.wallet_send import Ui_widget_wallet_send
from app.backend.api import Api


class WalletSend(QWidget, Ui_widget_wallet_send):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.api = Api()

        self.amount_validator = QDoubleValidator()
        balance = float(settings.value('balance', 0.00))
        self.amount_validator.setRange(0.00000001, balance, 8)

        self.updater = parent.updater
        self.updater.balance_changed.connect(self.on_balance_changed)

        self.edit_amount.setValidator(self.amount_validator)
        self.edit_amount.textChanged.connect(self.check_state)
        self.edit_amount.textChanged.emit(self.edit_amount.text())

        self.edit_address.setValidator(AddressValidator())
        self.edit_address.textChanged.connect(self.check_state)
        self.edit_address.textChanged.emit(self.edit_address.text())

        self.btn_send_cancel.clicked.connect(self.on_cancel_clicked)
        self.btn_send_send.clicked.connect(self.on_send_clicked)

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

    def on_cancel_clicked(self):
        self.edit_amount.clear()
        self.edit_address.clear()
        self.edit_description.clear()

    def on_send_clicked(self):
        amount = float(self.edit_amount.text().replace(',', '.'))
        success = self.api.send(address=self.edit_address.text(), amount=amount, description=self.edit_description.text())
        if success:
            self.edit_address.setText('')
            self.edit_amount.setText('')
            self.edit_description.setText('')
            self.updater.on_send()

    def on_balance_changed(self, balance):
        if balance is None:
            balance = float(settings.value('balance', 0.00))
        else:
            balance = float(settings.value('balance', balance))
        self.amount_validator.setRange(0.00000001, balance, 8)


