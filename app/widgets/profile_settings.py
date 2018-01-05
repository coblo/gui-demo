# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QMessageBox

from app.backend.rpc import RpcClient
from app.signals import signals
from app.ui.profile_settings import Ui_ProfileSettingsDialog
from app.models import Profile
from app.models.db import profile_session_scope


class ProfileSettingsDialog(QDialog, Ui_ProfileSettingsDialog):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.profile_name = kwargs.pop('profile')
        with profile_session_scope() as session:
            self.profile = session.query(Profile).filter(Profile.name == self.profile_name).first()
        self.setupUi(self)

        if self.profile is not None:
            self.label_title.setText('Editing Profile Settings For Profile "{}"'.format(self.profile.name))
        self.check_set_active.setHidden(self.profile is not None)
        self.is_tested = False

        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_reset.clicked.connect(self.reset_fields)
        self.btn_test_save.clicked.connect(self.on_test_or_save)

        self.reset_fields()

        self.setStyleSheet('QPushButton {padding: 5 12 5 12; font: 10pt "Roboto Light"}')
        self.btn_test_save.setStyleSheet(
            'QPushButton {background-color: #0183ea; color: white; padding: 5 12 5 12; font: 10pt "Roboto Light"}')

    def on_test_or_save(self):
        if self.is_tested:
            with profile_session_scope() as session:
                if self.profile is None:
                    profile = Profile(
                        name=self.edit_name.text(),
                        rpc_host=self.edit_host.text(),
                        rpc_port=int(self.edit_port.text()),
                        rpc_user=self.edit_rpc_user.text(),
                        rpc_password=self.edit_rpc_password.text(),
                        rpc_use_ssl=self.check_box_use_ssl.isChecked(),
                        manage_node=self.check_manage_node.isChecked(),
                        exit_on_close=self.check_exit_close.isChecked(),
                        active=False,
                        alias="",
                        address="",
                        balance=0,
                        is_admin=False,
                        is_miner=False
                    )
                    session.add(profile)
                    if self.check_set_active.isChecked():
                        profile.set_active(session)
                else:
                    session.query(Profile).filter(Profile.name == self.profile.name).update({
                        "name": self.edit_name.text(),
                        "rpc_host": self.edit_host.text(),
                        "rpc_port": int(self.edit_port.text()),
                        "rpc_user": self.edit_rpc_user.text(),
                        "rpc_password": self.edit_rpc_password.text(),
                        "rpc_use_ssl": self.check_box_use_ssl.isChecked(),
                        "manage_node": self.check_manage_node.isChecked(),
                        "exit_on_close": self.check_exit_close.isChecked()
                    })
                signals.profile_changed.emit()
            self.on_cancel()
        else:
            err_msg = False
            client = RpcClient(
                host=self.edit_host.text(),
                port=int(self.edit_port.text()),
                user=self.edit_rpc_user.text(),
                pwd=self.edit_rpc_password.text(),
                use_ssl=self.check_box_use_ssl.isChecked(),
            )
            try:
                response = client.getruntimeparams()
                if response['error'] is not None:
                    err_msg = response['error']
            except Exception as e:
                err_msg = str(e)
            if err_msg:
                error_dialog = QMessageBox()
                error_dialog.setWindowTitle('Connection Error')
                error_dialog.setText(err_msg)
                error_dialog.setIcon(QMessageBox.Warning)
                error_dialog.exec_()
            else:
                self.switch_test_mode(tested=True)

    def switch_test_mode(self, tested=False):
        self.is_tested = tested
        self.btn_test_save.setText('Save' if tested else 'Test Connection')
        self.edit_host.setDisabled(tested)
        self.edit_port.setDisabled(tested)
        self.edit_rpc_user.setDisabled(tested)
        self.edit_rpc_password.setDisabled(tested)
        self.check_manage_node.setDisabled(tested)
        self.check_box_use_ssl.setDisabled(tested)

    def on_cancel(self):
        self.close()

    def reset_fields(self):
        if self.is_tested:
            self.switch_test_mode(tested = False)
        if self.profile is None:
            self.edit_name.clear()
            self.edit_host.clear()
            self.edit_port.clear()
            self.edit_rpc_user.clear()
            self.edit_rpc_password.clear()
            self.check_box_use_ssl.setChecked(False)
            self.check_manage_node.setChecked(False)
            self.check_exit_close.setChecked(False)
            self.check_set_active.setChecked(False)
        else:
            self.edit_name.setText(self.profile.name)
            self.edit_host.setText(self.profile.rpc_host)
            self.edit_port.setText("{}".format(self.profile.rpc_port))
            self.edit_rpc_user.setText(self.profile.rpc_user)
            self.edit_rpc_password.setText(self.profile.rpc_password)
            self.check_box_use_ssl.setChecked(self.profile.rpc_use_ssl)
            self.check_manage_node.setChecked(self.profile.manage_node)
            self.check_exit_close.setChecked(self.profile.exit_on_close)
