# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets

from app.ui.skills import Ui_WidgetSkills
from app.updater import Updater


class WidgetSkills(QtWidgets.QGroupBox, Ui_WidgetSkills):

    ADMIN, CREATE, ISSUE, MINE = 'admin', 'create', 'issue', 'mine'
    SKILLS = (ADMIN, CREATE, ISSUE, MINE)

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.updater = parent.updater
        self.updater.permissions_changed.connect(self.on_skills_changed)

    def on_skills_changed(self, skills):
        for skill in self.SKILLS:
            label = getattr(self, 'lbl_{}'.format(skill))
            label.setEnabled(skill in skills)
            label.style().polish(label)


if __name__ == '__main__':
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    wrapper = QtWidgets.QWidget()
    wrapper.updater = Updater()
    wrapper.setLayout(QtWidgets.QHBoxLayout(wrapper))
    wrapper.layout().addWidget(WidgetSkills(wrapper))
    wrapper.updater.start()
    wrapper.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
