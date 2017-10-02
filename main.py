#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Main"""
import sys

from PyQt5.QtWidgets import QApplication

from ui.ui_main import Ui_Main

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Ui_Main()
    sys.exit(app.exec_())