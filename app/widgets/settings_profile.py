from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox

from app.ui.settings_profile import Ui_settings_profile

from app.models import Profile


class SettingsProfile(QtWidgets.QDialog, Ui_settings_profile):

    connection_settings_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        #todo: disable connection settings, when user does not manage node

        self.cb_profile.setHidden(True)
        self.btn_save_changed_profile.setHidden(True)
        self.btn_cancel_changed_profile.setHidden(True)

        self.active_profile = Profile.get_active()
        self.refill_profile_form(self.active_profile)
        self.profiles = Profile.select()

        for profile in self.profiles:
            self.cb_profile.addItem(profile.name)
        self.cb_profile.setCurrentText(self.active_profile.name)

        self.btn_add_profile.clicked.connect(self.on_add_profile)
        self.btn_change_profile.clicked.connect(self.on_change_profile)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_save_changed_profile.clicked.connect(self.on_save_change_profile)
        self.btn_cancel_changed_profile.clicked.connect(self.on_cancel_change_profile)

    def on_change_profile(self):
        self.switch_profile_change_view(True)

    def on_add_profile(self):
        self.refill_profile_form()
        self.switch_profile_add_view(True)

    def on_save_added_profile(self):
        # todo: save new profile (should it be active)
        self.switch_profile_add_view(False)
        self.refill_profile_form(profile=Profile.get_active())

    def on_reset_added_profile(self):
        self.switch_profile_add_view(False)
        self.refill_profile_form(profile=Profile.get_active())

    def on_save(self):
        # todo: save change of active profile
        pass

    def on_reset(self):
        self.refill_profile_form(profile=Profile.get_active())

    def on_save_change_profile(self):
        self.switch_profile_change_view(False)
        # todo: really change profile
        new_profile = Profile.select().where(Profile.name == self.cb_profile.currentText()).first()
        self.refill_profile_form(new_profile)

    def on_cancel_change_profile(self):
        self.switch_profile_change_view(False)

    def switch_profile_change_view(self, edit_mode=False):
        self.btn_change_profile.setHidden(edit_mode)
        self.btn_add_profile.setHidden(edit_mode)
        self.btn_save_changed_profile.setHidden(not edit_mode)
        self.btn_cancel_changed_profile.setHidden(not edit_mode)
        self.cb_profile.setHidden(not edit_mode)

    def switch_profile_add_view(self, add_mode=False):
        self.btn_change_profile.setHidden(add_mode)
        self.btn_add_profile.setHidden(add_mode)
        self.btn_reset.setText("Cancel" if add_mode else "Reset")
        self.btn_reset.clicked.connect(self.on_reset_added_profile if add_mode else self.on_reset)
        self.btn_save.clicked.connect(self.on_save_added_profile if add_mode else self.on_save)

    def refill_profile_form(self, profile=None):
        if profile is not None:
            self.label_text_profile.setText("You are editing")
            self.label_active_profile.setText("\"{}\"".format(profile.name))
            self.edit_name.setText(profile.name)
            self.edit_host.setText(profile.rpc_host)
            self.edit_port.setText(profile.rpc_port)
            self.edit_rpc_user.setText(profile.rpc_user)
            self.edit_rpc_password.setText(profile.rpc_password)
            self.check_box_use_ssl.setChecked(profile.rpc_use_ssl)
            self.check_manage_node.setChecked(profile.manage_node)

        else:
            self.label_text_profile.setText("You are adding a new profile")
            self.label_active_profile.setText("")
            self.edit_name.clear()
            self.edit_host.clear()
            self.edit_port.clear()
            self.edit_rpc_user.clear()
            self.edit_rpc_password.clear()
            self.check_box_use_ssl.setChecked(False)
            self.check_manage_node.setChecked(False)
