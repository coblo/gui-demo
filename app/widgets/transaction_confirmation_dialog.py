from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from app.models import Profile
from app.settings import Settings
from app.ui.transaction_confirmation_dialog import Ui_transaction_confirmation_dialog
from typing import Callable


class TransactionConfirmationDialog(QDialog, Ui_transaction_confirmation_dialog):

    fee = "YOU SHOULD NEVER SEE THIS"
    callback = None
    __settings = Settings()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.setFixedSize(self.size())

    def exec(self):
        if self.__settings.value('suppress_transaction_fee_warning', type=bool):
            self.callback()
        else:
            self.label.setText(self.label.text().replace("{fee}", self.fee))
            self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.__on_ok_click)
            super().exec()

    def __on_ok_click(self):

        if not self.__settings.value('suppress_transaction_fee_warning', type=bool) and self.checkBox.isChecked():
            self.__settings.setValue('suppress_transaction_fee_warning', True)
        self.callback()
