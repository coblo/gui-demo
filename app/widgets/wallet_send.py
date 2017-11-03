from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QWidget
from decimal import Decimal

from app.backend.rpc import get_active_rpc_client
from app.tools.validators import AddressValidator
from app.ui.wallet_send import Ui_widget_wallet_send


class WalletSend(QWidget, Ui_widget_wallet_send):

    amount_symbols = '0123456789.'

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.edit_amount.textChanged.connect(self.on_amount_edit)

        self.edit_address.setValidator(AddressValidator())
        self.edit_address.textChanged.connect(self.check_state)

        self.edit_description.setStyleSheet('QLineEdit:focus {background-color: #fff79a}')

        self.btn_send_cancel.clicked.connect(self.on_cancel_clicked)
        self.btn_send_send.clicked.connect(self.on_send_clicked)

    def on_amount_edit(self, text):
        if not text:
            self.edit_amount.setStyleSheet('QLineEdit {background-color: #fff79a}')
            return
        text = '0.' if text == '.' else text
        clean = ''.join(c for c in text.replace(',', '.') if c in self.amount_symbols)
        shifter = []
        dot_found = False
        for c in reversed(clean):
            if c != ".":
                shifter.append(c)
            else:
                if dot_found is False:
                    shifter.append(c)
                    dot_found = True
        clean = ''.join(reversed(shifter))
        self.edit_amount.setText(clean)
        try:
            amount = Decimal(clean)
        except Exception as e:
            return
        if amount > self.parent().profile.balance or abs(amount.as_tuple().exponent) > 8:
            self.edit_amount.setStyleSheet('QLineEdit { background-color: #f6989d}')
        else:
            self.edit_amount.setStyleSheet('QLineEdit { background-color: #c4df9b}')

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client = get_active_rpc_client()
        try:
            response = client.send(
                address=self.edit_address.text(),
                amount=Decimal(self.edit_amount.text()),
                comment=self.edit_description.text()
            )
            if response['error'] is not None:
                err_msg = response['error']['message']
                raise RuntimeError(err_msg)
            self.on_cancel_clicked()
            QApplication.restoreOverrideCursor()
        except Exception as e:
            err_msg = str(e)
            error_dialog = QMessageBox()
            error_dialog.setWindowTitle('Error while sending')
            error_dialog.setText(err_msg)
            error_dialog.setIcon(QMessageBox.Warning)
            QApplication.restoreOverrideCursor()
            error_dialog.exec_()

