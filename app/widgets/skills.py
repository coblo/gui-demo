# -*- coding: utf-8 -*-
import time
from PyQt5 import QtWidgets, QtCore
from app.ui.skills import Ui_WidgetSkills
from app.backend.rpc import client


class WidgetSkills(QtWidgets.QGroupBox, Ui_WidgetSkills):

    ADMIN, CREATE, ISSUE, MINE = 'admin', 'create', 'issue', 'mine'
    SKILLS = (ADMIN, CREATE, ISSUE, MINE)

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.lbl_admin.setEnabled(True)
        self.lbl_admin.setDisabled(True)
        self.updater = SkillsUpdater(self)
        self.updater.skills_changed.connect(self.on_skills_changed)
        self.updater.start()

    def on_skills_changed(self, skills):
        for skill in self.SKILLS:
            label = getattr(self, 'lbl_{}'.format(skill))
            label.setEnabled(skill in skills)
            label.style().polish(label)


class SkillsUpdater(QtCore.QThread):

    UPDATE_INTERVALL = 10
    skills_changed = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_skills = []

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            try:
                address = client.getruntimeparams()['result']['handshakelocal']
                resp = client.listpermissions('mine,admin,create,issue', address)
                skills = []
                for entry in resp['result']:
                    skills.append(entry['type'])
            except Exception:
                skills = []

            if skills != self.last_skills:
                self.skills_changed.emit(skills)
                self.last_skills = skills

            time.sleep(self.UPDATE_INTERVALL)


if __name__ == '__main__':
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    window = WidgetSkills(None)
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
