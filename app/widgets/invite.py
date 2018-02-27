# -*- coding: utf-8 -*-
import logging
from PyQt5 import QtGui
from binascii import hexlify

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QMessageBox

from app.signals import signals
from app.tools.address import address_valid
from app.tools.validators import AddressValidator
from app.ui.invite import Ui_dlg_invite
from app.backend.rpc import get_active_rpc_client


log = logging.getLogger(__name__)


class InviteDialog(QDialog, Ui_dlg_invite):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.bbox_invite.accepted.connect(self.on_accepted)

        self.setStyleSheet('QPushButton {padding: 5 12 5 12; font: 10pt "Roboto Light"}')
        send_button = self.bbox_invite.button(QDialogButtonBox.Ok)
        assert isinstance(send_button, QPushButton)
        send_button.setText("Send Invitation")

        address = self.edit_candidate_address
        address.setValidator(AddressValidator(address))
        address.textChanged.connect(self.on_textChanged)

    @pyqtSlot()
    def on_accepted(self):
        log.debug('sending invite...')

        address = self.edit_candidate_address.text()

        # TODO: check if address already has permissions

        if not address_valid(address):
            return QMessageBox.critical(self, 'Invalid Address', 'Invalid Address')

        perms = []
        if self.cbox_grant_guardian_skills.isChecked():
            perms.append('admin')
        if self.cbox_grant_validator_skills.isChecked():
            perms.append('mine')

        perms = ','.join(perms)
        comment = self.edit_public_comment.text()
        if comment:
            comment = hexlify(comment.encode('utf-8')).decode('utf-8')
        else:
            comment = ''
        log.debug('granting %s to %s - reason: %s' % (perms, address, comment))
        client = get_active_rpc_client()
        try:
            client.grantwithdata(address, perms, comment)

            self.edit_candidate_address.clear()
            self.edit_candidate_address.setStyleSheet('QLineEdit { background-color: #fff }')
            self.edit_public_comment.clear()
            self.cbox_grant_validator_skills.setChecked(True)
            self.cbox_grant_guardian_skills.setChecked(False)

            signals.new_unconfirmed.emit('vote')
        except Exception as e:
            return QMessageBox.critical(self, 'Error sending invitation', "{}".format(e))

    @pyqtSlot(str)
    def on_textChanged(self, text):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'  # green
        elif state == QtGui.QValidator.Intermediate:
            color = '#fff79a'  # yellow
        else:
            color = '#f6989d'  # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)


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
    dialog = InviteDialog()
    dialog.show()
    sys.exit(app.exec())
