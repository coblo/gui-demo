# -*- coding: utf-8 -*-
import logging

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QWidget
from peewee import fn

from app.backend.rpc import get_active_rpc_client
from app.models import Address, Alias, data_db
from app.ui.dialog_change_alias import Ui_dialog_change_alias
from app.models import Profile
from app.signals import signals
from app.tools.validators import username_regex

log = logging.getLogger(__name__)


class ChangeAlias(QDialog, Ui_dialog_change_alias):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        from app.models.db import profile_session_scope
        with profile_session_scope() as session:
            self.profile = Profile.get_active(session)
        self.on_profile_changed(self.profile)

        self.edit_alias.setText(self.profile.alias)
        self.edit_alias.textChanged.connect(self.on_alias_changed)

        signals.profile_changed.connect(self.on_profile_changed)
        self.adjustSize()
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save)
        self.buttonBox.button(QDialogButtonBox.Save).setDisabled(True)

    @pyqtSlot(Profile)
    def on_profile_changed(self, new_profile):
        self.profile = new_profile
        self.edit_alias.setText(new_profile.alias)

    def on_alias_changed(self, text):
        from app.models.db import data_session_scope
        text = text.lower()
        self.edit_alias.setText(text.lower())
        is_valid = False
        with data_session_scope() as session:
            if not username_regex.match(text):
                self.lbl_error.setText('- It may contain alphanumerical characters and "_", ".", "-"\n'
                                       '- It must not start or end with "-" or "."\n'
                                       '- It must be between 3 and 30 characters\n'
                                       '- It must not have consecutive "_", ".", "-" characters')
            elif text != self.profile.alias and Alias.alias_in_use(session, text):
                self.lbl_error.setText('Username already in use.')
            else:
                self.lbl_error.setText("")
                self.adjustSize()
                is_valid = True
        self.buttonBox.button(QDialogButtonBox.Save).setDisabled(not is_valid)

    def save(self):
        client = get_active_rpc_client()
        try:
            response = client.publish(
                stream='alias',
                key=self.edit_alias.text(),
                hex_data=''
            )
            if response['error'] is not None:
                err_msg = response['error']['message']
                raise RuntimeError(err_msg)
            else:
                QMessageBox.information(QWidget(), 'Changing alias successful',
                                        'The transaction to change your alias was sent successful. It may take some'
                                        ' minutes to validate your transaction. After validation your alias will be'
                                        ' changed.', QMessageBox.Ok, QMessageBox.Ok)
        except Exception as e:
            err_msg = str(e)
            error_dialog = QMessageBox()
            error_dialog.setWindowTitle('Error while changing alias')
            error_dialog.setText(err_msg)
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.exec_()
        self.close()
