# -*- coding: utf-8 -*-
import logging

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot

from decimal import Decimal, ROUND_DOWN
from app.ui.my_account import Ui_MyAccount
from app.models import Profile, init_profile_db
from app.signals import signals
from app import CURRENCY_CODE


log = logging.getLogger(__name__)


class MyAccount(QWidget, Ui_MyAccount):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.profile = Profile.get_active()
        self.on_profile_changed(self.profile)

        signals.profile_changed.connect(self.on_profile_changed)

        self.btn_wallet_alias_edit_save.hide()
        self.btn_wallet_alias_edit_cancel.hide()
        self.edit_alias.hide()

        self.btn_wallet_alias_edit_start.clicked.connect(self.start_edit_alias)
        self.btn_wallet_alias_edit_cancel.clicked.connect(self.stop_edit_alias)
        self.btn_wallet_alias_edit_save.clicked.connect(self.save_alias)
        self.edit_alias.returnPressed.connect(self.save_alias)
        self.lbl_wallet_address.setText(self.profile.address)

    @pyqtSlot(Profile)
    def on_profile_changed(self, new_profile):
        self.profile = new_profile
        self.lbl_wallet_alias.setText(self.profile.alias)
        self.edit_alias.setText(self.profile.alias)
        self.lbl_wallet_address.setText(self.profile.address)

        # minimal amount for changing the alias
        if self.profile.balance < 0.00001:
            self.stop_edit_alias()
            self.btn_wallet_alias_edit_start.setEnabled(False)
        else:
            self.btn_wallet_alias_edit_start.setEnabled(True)

        normalized = self.profile.balance.quantize(Decimal('.01'), rounding=ROUND_DOWN)
        display = "{0:n} {1}".format(normalized, CURRENCY_CODE)
        self.lbl_wallet_balance.setText(display)
        self.lbl_wallet_balance.setToolTip("{0:n} {1}".format(
            self.profile.balance, CURRENCY_CODE)
        )

    def format_balance(self, balance):
        display = "{0:n}".format(balance.normalize()) if balance is not ' ' else balance
        return display + ' CHM'

    def start_edit_alias(self):
        self.lbl_wallet_alias.hide()
        self.btn_wallet_alias_edit_start.hide()
        self.btn_wallet_alias_edit_save.show()
        self.btn_wallet_alias_edit_cancel.show()
        self.edit_alias.show()
        self.edit_alias.setFocus()
        self.edit_alias.selectAll()

    def stop_edit_alias(self):
        self.lbl_wallet_alias.setText(self.profile.alias)
        self.edit_alias.setText(self.profile.alias)
        self.lbl_wallet_alias.show()
        self.btn_wallet_alias_edit_start.show()
        self.btn_wallet_alias_edit_save.hide()
        self.btn_wallet_alias_edit_cancel.hide()
        self.edit_alias.hide()

    def save_alias(self):
        try:
            self.profile.update_alias(self.edit_alias.text())
            self.stop_edit_alias()
            QMessageBox().information(self, "New alias", "New alias registration in progress")
        except Exception as e:
            QMessageBox().critical(self, 'Alias update error', str(e))

if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    from app import helpers
    from app import models
    helpers.init_logging()
    helpers.init_data_dir()
    models.init_profile_db()
    models.init_data_db()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('fusion')
    wgt = MyAccount()
    wgt.show()
    sys.exit(app.exec())
