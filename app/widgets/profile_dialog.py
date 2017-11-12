from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from app.ui.profile_dialog import Ui_ProfileDialog

from app.models import Profile


class ProfileDialog(QtWidgets.QDialog, Ui_ProfileDialog):

    connection_settings_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        self.setupUi(self)

        if profile is not None:
            try:
                self.profile = Profile.select().where(Profile.name == profile).first()
            except Exception as e:
                err_msg = str(e)
                error_dialog = QMessageBox()
                error_dialog.setWindowTitle('Error while searching profile')
                error_dialog.setText(err_msg)
                error_dialog.setIcon(QMessageBox.Warning)
                error_dialog.exec_()
                self.close()

            self.setWindowTitle('Edit Profile')
            self.label_title.setText('Edit Profile')

            self.edit_name.setText(self.profile.name)
            self.edit_host.setText(self.profile.rpc_host)
            self.edit_port.setText(self.profile.rpc_port)
            self.edit_rpc_user.setText(self.profile.rpc_user)
            self.edit_rpc_password.setText(self.profile.rpc_password)

            self.check_box_use_ssl.setChecked(self.profile.rpc_use_ssl)
            self.check_manage_node.setChecked(self.profile.manage_node)

    def on_accept(self):
        print('saved')
