from PyQt5 import QtWidgets

from PyQt5.QtWidgets import QDialogButtonBox
from app.backend.models import Profile

from app import settings
from app.ui.connection_settings import Ui_ConnectionSettingsDialog


class ConnectionSettingsDialog(QtWidgets.QDialog, Ui_ConnectionSettingsDialog):

    fields = 'chain', 'host', 'port', 'rpc_user', 'rpc_password'
    prefix = 'profile/default/{}'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        p_obj = Profile.get_active()
        if p_obj is None:
            self.combo_profile.addItem('Default')
        else:
            for p_obj in Profile.select():
                self.combo_profile.addItem(p_obj.name)
            self.set_form_data(p_obj)

        # self.load_connection_settings()
        self.btn_profile_add.clicked.connect(self.on_profile_add)
        self.btn_profile_delete.clicked.connect(self.on_profile_delete)
        self.combo_profile.currentTextChanged.connect(self.on_profile_select)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

    def set_form_data(self, p_obj):
        self.edit_chain.setText(p_obj.chain)
        self.edit_host.setText(p_obj.host)
        self.edit_port.setText(str(p_obj.port))
        self.edit_rpc_user.setText(p_obj.username)
        self.edit_rpc_password.setText(p_obj.password)
        self.check_box_use_ssl.setChecked(p_obj.use_ssl)
        self.check_manage_node.setChecked(p_obj.manage_node)

    def profile_from_form(self):
        name = self.combo_profile.currentText()
        p_obj, created = Profile.get_or_create(name=name)
        p_obj.chain = self.edit_chain.text()
        p_obj.host = self.edit_host.text()
        p_obj.port = self.edit_port.text()
        p_obj.username = self.edit_rpc_user.text()
        p_obj.password = self.edit_rpc_password.text()
        p_obj.use_ssl = self.check_box_use_ssl.isChecked()
        p_obj.manage_node = self.check_manage_node.isChecked()
        p_obj.active = True
        return p_obj

    def load_connection_settings(self):
        for field in self.fields:
            val = settings.value(self.prefix.format(field), None)
            if val is not None:
                edit_widget = getattr(self, 'edit_{}'.format(field))
                edit_widget.setText(val)

        use_ssl = settings.value(self.prefix.format('use_ssl'), False)
        self.check_box_use_ssl.setChecked(use_ssl)

    def save_connection_settings(self):
        for field in self.fields:
            edit_widget = getattr(self, 'edit_{}'.format(field))
            settings.setValue(self.prefix.format(field), edit_widget.text())
        settings.setValue(self.prefix.format('use_ssl'), self.check_box_use_ssl.checkState())
        settings.sync()

    def on_profile_add(self):
        profile_name, ok_pressed = QtWidgets.QInputDialog.getText(
            self, 'Create profile', 'Profile name:', QtWidgets.QLineEdit.Normal
        )
        if ok_pressed:
            self.combo_profile.addItem(profile_name)
            self.combo_profile.setCurrentText(profile_name)

    def on_profile_delete(self):
        profile_name = self.combo_profile.currentText()
        p_obj, created = Profile.get_or_create(name=profile_name)
        Profile.delete_instance(p_obj)
        self.combo_profile.addItem()
        self.combo_profile.removeItem()
        self.combo_profile.setCurrentIndex(0)

    def on_profile_select(self, name):
        p_obj, created = Profile.get_or_create(name=name)
        self.set_form_data(p_obj)


    def apply(self):
        self.profile_from_form().save()
        self.close()
        # self.save_connection_settings()


    def reset(self):
        for line_edit in self.findChildren(QtWidgets.QLineEdit):
            line_edit.clear()


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(ConnectionSettingsDialog)
