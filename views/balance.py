#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Widget that shows and update wallet balance"""
import sys
import time
import traceback
from PyQt5 import QtCore, QtGui, QtWidgets
from views.rpc import client


class BalanceUpdater(QtCore.QThread):
    """
    A separate thread that polls the node for balance updates.
    """

    # Signals
    new_balance = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(BalanceUpdater, self).__init__(parent)

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            balance = client.getbalance()
            balance = '???.??' if balance is None else str(balance)
            self.new_balance.emit(balance)
            time.sleep(1)


class BalanceWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName('BalanceWidget')
        # self.setWindowTitle('Balance')
        self.balance = QtWidgets.QLabel('???.??')
        self.setup_ui()
        self.balance_updater = BalanceUpdater(self)
        self.balance_updater.new_balance.connect(self.on_new_balance)
        self.balance_updater.start()

    def setup_ui(self):
        self.setAutoFillBackground(False)
        self.setStyleSheet("""
            QWidget {
                background-color: #333745;
                color: white;
                font-family: Droid Sans;               
            }
            #LabelBalance {
                color: grey;
                font-size: 13px;
                font-weight: 400;
            }
            #LabelBalanceAmount {
                color: white;
                font-size: 36px;
                font-weight: 700;
            }
            #LabelCurrency {
                color: grey;
                font-size: 13px;
                font-weight:400;
                margin-top: 2px;
            }
        """)

        title = QtWidgets.QLabel('Total Balance:')
        title.setObjectName('LabelBalance')
        self.balance.setObjectName('LabelBalanceAmount')
        self.balance.setAlignment(QtCore.Qt.AlignTop)
        currency = QtWidgets.QLabel('CHM')
        currency.setObjectName('LabelCurrency')
        currency.setAlignment(QtCore.Qt.AlignTop)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(QtCore.Qt.AlignRight)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(10, 10, 10, 10)

        amount_layout = QtWidgets.QHBoxLayout()
        amount_layout.addWidget(self.balance)
        amount_layout.addWidget(currency)

        main_layout.addWidget(title)

        main_layout.addLayout(amount_layout)
        main_layout.addSpacerItem(spacer)

        self.setLayout(main_layout)

    @QtCore.pyqtSlot(str, name='new_balance')
    def on_new_balance(self, balance):
        self.balance.setText(balance)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    QtGui.QFontDatabase.addApplicationFont('resources/DroidSans-Bold.ttf')
    QtGui.QFontDatabase.addApplicationFont('resources/DroidSans-Regular.ttf')
    window = BalanceWidget()
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
