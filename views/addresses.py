#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Widget that shows and updates wallet addresses"""
import sys
import time
import traceback
from PyQt5 import QtCore, QtGui, QtWidgets
from views.rpc import client


class AddressesWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AddressesWidget')
        self.setAutoFillBackground(False)

        title = QtWidgets.QLabel('My Addresses')
        table = QtWidgets.QTableWidget(1, 2)
        table.setObjectName('AddressTable')
        table.setHorizontalHeaderLabels(('Address', 'Balance'))

        btn_new_address = QtWidgets.QPushButton('Create new address')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(table)
        layout.addWidget(btn_new_address)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    QtGui.QFontDatabase.addApplicationFont('resources/DroidSans-Bold.ttf')
    QtGui.QFontDatabase.addApplicationFont('resources/DroidSans-Regular.ttf')
    window = AddressesWidget()
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
