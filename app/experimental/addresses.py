#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Widget that shows and updates wallet addresses"""
import sys
import time
import traceback
from PyQt5 import QtCore, QtGui, QtWidgets
from app.resources import resources_rc

from app.backend.rpc import client


class AddressUpdater(QtCore.QThread):

    addresses_updated = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(AddressUpdater, self).__init__(parent)
        self.last_address_balances = None

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            address_balances = client.getmultibalances()
            if address_balances:
                if address_balances != self.last_address_balances:
                    self.addresses_updated.emit(address_balances)
                    self.last_address_balances = address_balances
            time.sleep(3)


class AddressesWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AddressesWidget')
        self.setAutoFillBackground(False)

        title = QtWidgets.QLabel('My Addresses')
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setObjectName('AddressTable')
        self.table.verticalHeader().setVisible(False)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalHeaderLabels(('Address', 'Balance'))
        self.table.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)

        btn_new_address = QtWidgets.QPushButton('Create new address')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.table)
        layout.addWidget(btn_new_address)
        self.setLayout(layout)

        self.address_updater = AddressUpdater(self)
        self.address_updater.addresses_updated.connect(self.on_addresses_updated)
        self.address_updater.start()

    @QtCore.pyqtSlot(list, name='addresses_updated')
    def on_addresses_updated(self, address_balances):
        self.table.setRowCount(len(address_balances))

        for idx, ab in enumerate(address_balances):
            address, balance = ab
            address = QtWidgets.QTableWidgetItem(address)
            balance = QtWidgets.QTableWidgetItem(str(balance))
            self.table.setItem(idx, 0, address)
            self.table.setItem(idx, 1, balance)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.adjustSize()
        self.setMinimumWidth(self.width())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    QtGui.QFontDatabase.addApplicationFont(':/fonts/DroidSans-Bold.ttf.ttf')
    QtGui.QFontDatabase.addApplicationFont(':/fonts/DroidSans-Regular.ttf')
    window = AddressesWidget()
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
