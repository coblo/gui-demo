from PyQt5.QtWidgets import QDialog
from app.ui.apply import Ui_ApplyDialog


class ApplyDialog(QDialog, Ui_ApplyDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
