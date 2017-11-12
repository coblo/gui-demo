from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from app.ui.settings_profile import Ui_settings_profile

from app.models import Profile


class SettingsProfile(QtWidgets.QDialog, Ui_settings_profile):

    connection_settings_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.cb_profile.setHidden(True)

        self.profile = Profile.get_active()
        self.label_active_profile.setText(self.profile.name)

        self.edit_name.setText(self.profile.name)
        self.edit_host.setText(self.profile.rpc_host)
        self.edit_port.setText(self.profile.rpc_port)
        self.edit_rpc_user.setText(self.profile.rpc_user)
        self.edit_rpc_password.setText(self.profile.rpc_password)

        self.check_box_use_ssl.setChecked(self.profile.rpc_use_ssl)
        self.check_manage_node.setChecked(self.profile.manage_node)

        self.btn_add_profile.clicked.connect(self.on_add_profile)
        self.btn_change_profile.clicked.connect(self.on_change_profile)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_reset.clicked.connect(self.on_reset)

    def on_change_profile(self):
        pass

    def on_add_profile(self):
        pass

    def on_save(self):
        pass

    def on_reset(self):
        pass