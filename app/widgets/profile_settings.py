# -*- coding: utf-8 -*-
import logging

from PyQt5.QtWidgets import QDialog

from app.ui.profile_settings import Ui_Profile_settings

from app.models import Profile
from app.widgets.profile_dialog import ProfileDialog


log = logging.getLogger(__name__)


class ProfileSettings(QDialog, Ui_Profile_settings):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        combobox = self.cb_profile
        for index, profile in enumerate(Profile.select()):
            combobox.addItem(profile.name)
        combobox.setCurrentText(Profile.get_active().name)

        self.btn_add_profile.clicked.connect(lambda: self.on_edit_profile('add'))
        self.btn_edit_profile.clicked.connect(lambda: self.on_edit_profile('edit'))

        self.cb_profile.currentIndexChanged.connect(self.on_change_profile)

    def on_edit_profile(self, action):
        profile = None
        if action == 'edit':
            profile = self.cb_profile.currentText()
        profile_dialog = ProfileDialog(self, profile)
        profile_dialog.exec_()

    def on_change_profile(self):
        pass
