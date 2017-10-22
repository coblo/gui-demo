# -*- coding: utf-8 -*-
"""Input Validation Classes"""
from app.application import Application


def run_widget(widget):
    import sys
    import traceback
    import compile_ui
    compile_ui.ui()
    compile_ui.resource()
    app = Application(sys.argv, widget)
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
