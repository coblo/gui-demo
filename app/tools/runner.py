# -*- coding: utf-8 -*-
"""Input Validation Classes"""
from PyQt5 import QtWidgets


def run_widget(widget):
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    window = widget(None)
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
