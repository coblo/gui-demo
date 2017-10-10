from PyQt5.QtWidgets import QWidget
from app.ui.community import Ui_widget_community


class Community(QWidget, Ui_widget_community):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.btn_request_privileges.clicked.connect(lambda: parent.change_stack_index(2))
        self.updater = parent.updater
        self.updater.permissions_changed.connect(self.on_permissions_changed)

    def on_permissions_changed(self, perms):

        if 'admin' in perms:
            self.btn_validator_active.setText('Review Existing Validators')
            self.btn_gaurdian_active.setText('Review Existing Guardians')
            self.label_is_guardian.setText('Yes')
        else:
            self.widget_privilege_requests.setHidden(True)
            self.label_is_guardian.setText('No')

        if 'admin' in perms and 'mine' in perms:
            self.btn_request_privileges.setHidden(True)
        else:
            self.btn_request_privileges.setHidden(False)

        if 'mine' in perms:
            self.label_is_validator.setText('Yes')
        else:
            self.label_is_validator.setText('No')
