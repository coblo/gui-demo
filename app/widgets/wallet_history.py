from PyQt5 import QtWidgets, QtCore
from app.backend.updater import Updater
from app.ui.wallet_history import Ui_widget_wallet_history


class WalletHistory(QtWidgets.QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)


class TransactionHistoryTableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent):
        super().__init__(parent)
        self._data = ['Some', 'Test', 'Data', 'Here']
        self._header = ['Date', 'Description', 'Amount', 'Balance']

    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

if __name__ == '__main__':
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    wrapper = QtWidgets.QWidget()
    wrapper.updater = Updater()
    wrapper.setLayout(QtWidgets.QHBoxLayout(wrapper))
    wrapper.layout().addWidget(WalletHistory(wrapper))
    wrapper.updater.start()
    wrapper.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
