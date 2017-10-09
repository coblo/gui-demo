from PyQt5.QtWidgets import QWidget
from app.ui.create_privilege_request import Ui_widget_create_privilege_request
from app.backend.api import Api


class CreatePrivilegeRequest(QWidget, Ui_widget_create_privilege_request):
    def __init__(self, parent, change_stack_index):
        super().__init__(parent)
        self.api = Api()
        self.setupUi(self)