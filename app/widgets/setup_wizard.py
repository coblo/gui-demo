# -*- coding: utf-8 -*-
import logging

from PyQt5.QtGui import QPixmap

from app.ui.setup_wizard import Ui_SetupWizard
from PyQt5.QtWidgets import QWizard
from app.ui import resources_rc

log = logging.getLogger(__name__)


class SetupWizard(QWizard, Ui_SetupWizard):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    # import app
    # app.init()
    wrapper = QtWidgets.QApplication(sys.argv)
    wrapper.setStyle('fusion')
    wizard = SetupWizard()
    wizard.show()
    sys.exit(wrapper.exec())

