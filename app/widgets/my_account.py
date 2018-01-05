# -*- coding: utf-8 -*-
import logging

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot

from decimal import Decimal, ROUND_DOWN

from app.models import profile_session_scope
from app.ui.my_account import Ui_MyAccount
from app.models import Profile, init_profile_db
from app.signals import signals
from app import CURRENCY_CODE


log = logging.getLogger(__name__)


class MyAccount(QWidget, Ui_MyAccount):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.on_profile_changed()

        signals.profile_changed.connect(self.on_profile_changed)

    @pyqtSlot()
    def on_profile_changed(self):
        with profile_session_scope() as session:
            self.profile = Profile.get_active(session)
        self.lbl_wallet_alias.setText(self.profile.alias)
        self.lbl_wallet_address.setText(self.profile.address)

        normalized = self.profile.balance.quantize(Decimal('.01'), rounding=ROUND_DOWN)
        display = "{0:n} {1}".format(normalized, CURRENCY_CODE)
        self.lbl_wallet_balance.setText(display)
        self.lbl_wallet_balance.setToolTip("{0:n} {1}".format(
            self.profile.balance, CURRENCY_CODE)
        )


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
