from PyQt5.QtWidgets import QWidget
from app.ui.community import Ui_widget_community
from app.backend.api import Api


class Community(QWidget, Ui_widget_community):
    def __init__(self, parent):
        super().__init__(parent)
        self.api = Api()
        self.setupUi(self)
        if self.api.is_admin():
            self.btn_validator_active.setText('Review Existing Validators')
            self.btn_gaurdian_active.setText('Review Existing Guardians')
            self.label_is_guardian.setText('Yes')
        else:
            self.widget_privilege_requests.setHidden(True)
        if self.api.is_admin() and self.api.is_miner():
            self.btn_request_privileges.setHidden(True)
        if self.api.is_miner():
            self.label_is_validator.setText('Yes')