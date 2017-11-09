# -*- coding: utf-8 -*-
import logging
from PyQt5 import QtGui

from PyQt5.QtWidgets import QDialog

from app.ui.profile_settings import Ui_Profile_settings


log = logging.getLogger(__name__)


class ProfileSettings(QDialog, Ui_Profile_settings):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)