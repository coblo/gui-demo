from PyQt5 import QtWidgets

from PyQt5.QtWidgets import QDialogButtonBox

from app import settings
from app.ui.connection_settings import Ui_ConnectionSettingsDialog


class ConnectionSettingsDialog(QtWidgets.QDialog, Ui_ConnectionSettingsDialog):

    fields = 'chain', 'host', 'port', 'rpc_user', 'rpc_password'
    prefix = 'profile/default/{}'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.load_connection_settings()
        self.button_box.button(QDialogButtonBox.Reset).clicked.connect(self.reset)

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

    def accept(self):
        self.save_connection_settings()
        super().accept()

    def reset(self):
        for line_edit in self.findChildren(QtWidgets.QLineEdit):
            line_edit.clear()


if __name__ == '__main__':
    from app.tools.runner import run_widget
    run_widget(ConnectionSettingsDialog)
