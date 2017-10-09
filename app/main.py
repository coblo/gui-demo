#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Application Main Window and Entry Point"""
import qdarkstyle
import sys
import traceback
from PyQt5 import QtWidgets
from app.ui.main import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_group_nav.buttonClicked.connect(self.on_nav_change)

    def on_nav_change(self, btn):
        name = btn.objectName()
        if name == 'btn_nav_wallet':
            self.stack_content.setCurrentIndex(0)
        if name == 'btn_nav_community':
            self.stack_content.setCurrentIndex(1)
        if name == 'btn_nav_settings':
            self.stack_content.setCurrentIndex(2)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    sys.excepthook = traceback.print_exception
    main()
