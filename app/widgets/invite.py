# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QPushButton

from app.ui.invite import Ui_dlg_invite


class InviteDialog(QDialog, Ui_dlg_invite):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.setStyleSheet('QPushButton {padding: 5 12 5 12; font: 10pt "Roboto Light"}')
        send_button = self.bbox_invite.button(QDialogButtonBox.Ok)
        assert isinstance(send_button, QPushButton)
        send_button.setText("Send Invitation")


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle('fusion')
    dialog = InviteDialog()
    dialog.show()
    sys.exit(app.exec())
