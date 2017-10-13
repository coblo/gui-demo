from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHeaderView, QWidget

from app.ui.wallet_history import Ui_widget_wallet_history


class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.updater = parent.updater
        self.updater.transactions_changed.connect(self.on_transactions_changed)

    def on_transactions_changed(self, transactions):
        table_model = TransactionHistoryTableModel(['Date', 'Description', 'Amount', 'Balance'], transactions)
        self.table_wallet_history.setModel(table_model)
        header = self.table_wallet_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)


class TransactionHistoryTableModel(QAbstractTableModel):

    def __init__(self, header, transactions, parent=None):
        super().__init__()
        self.header = header
        self.transactions = transactions
        self.data = [transaction['data'] for transaction in transactions]
        self.unconfirmed = [index for index, transaction in enumerate(transactions) if not transaction['confirmed']]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.data)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.data[0])

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.data[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return QVariant(self.arraydata[index.row()][index.column()])
        elif role == Qt.TextAlignmentRole and index.column() != 1:
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.ForegroundRole:
            if index.column() == 2 and float(self.data[index.row()][2]) > 0:
                return QVariant(QColor(Qt.green))
            if index.column() == 2 and float(self.data[index.row()][2]) < 0:
                return QVariant(QColor(Qt.red))
            elif index.row() in self.unconfirmed:
                return QVariant(QColor(Qt.red))
        return None

    def sort(self, p_int, order=None):
        self.layoutAboutToBeChanged.emit()
        if p_int == 2:
            self.data = sorted(self.data, key=lambda x: abs(float(x[p_int])), reverse=(order == Qt.DescendingOrder))
        elif p_int == 3:
            self.data = sorted(self.data, key=lambda x: float(x[p_int]), reverse=(order == Qt.DescendingOrder))
        else:
            self.data = sorted(self.data, key=lambda x: x[p_int], reverse=(order == Qt.DescendingOrder))
        self.unconfirmed = [self.data.index(transaction['data']) for transaction in self.transactions if not transaction['confirmed']]
        self.layoutChanged.emit()