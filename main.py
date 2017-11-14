#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Main application entry point"""
import sys
import traceback
from app.signals import signals
from PyQt5.QtCore import QTimer


if __name__ == '__main__':
    from app.application import Application
    sys.excepthook = traceback.print_exception

    # emit signal when eventloop is started
    QTimer.singleShot(0, signals.application_start)

    sys.exit(Application(sys.argv).exec())
