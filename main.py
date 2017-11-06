#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Main application entry point"""
import sys
import traceback
from app.ui import resources_rc


if __name__ == '__main__':
    from app.application import Application
    sys.excepthook = traceback.print_exception
    sys.exit(Application(sys.argv).exec())
