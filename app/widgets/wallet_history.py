from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHeaderView, QWidget
from decimal import Decimal, ROUND_DOWN

from app.ui.wallet_history import Ui_widget_wallet_history


class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.updater = parent.updater
        self.table_model = TransactionHistoryTableModel(self)
        self.table_wallet_history.setModel(self.table_model)
        header = self.table_wallet_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)


class TransactionHistoryTableModel(QAbstractTableModel):

    DATETIME = 0
    DESCRIPTION = 1
    AMOUNT = 2
    BALANCE = 3
    CONFIRMATIONS = 4
    TXID = 5

    def __init__(self, parent=None):
        super().__init__()
        self.updater = parent.updater
        self.updater.transactions_changed.connect(self.on_transactions_changed)
        self.header = ['Date', 'Description', 'Amount', 'Balance']
        self.txs = []

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.txs)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.header)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def data(self, index, role=Qt.DisplayRole):
        row, col = index.row(), index.column()
        tx = self.txs[row]
        if role == Qt.DisplayRole:
            value = tx[col]
            if isinstance(value, Decimal):
                return str(value.quantize(Decimal('.01'), rounding=ROUND_DOWN))
            return str(value)
        if role == Qt.ToolTipRole and col in (self.AMOUNT, self.BALANCE):
            return str(tx[col])
        elif role == Qt.TextAlignmentRole and col != self.DESCRIPTION:
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.ForegroundRole:
            if col == self.AMOUNT and tx.amount > 0:
                return QVariant(QColor(Qt.green))
            if col == self.AMOUNT and tx.amount < 0:
                return QVariant(QColor(Qt.red))
        elif role == Qt.BackgroundColorRole:
            if tx.confirmations == 0:
                return QVariant(QColor(Qt.red))
            elif 1 <= tx.confirmations <= 3:
                return QVariant(QColor(Qt.yellow))
            return QVariant(QColor(Qt.white))
        return None

    def sort(self, p_int, order=None):
        self.layoutAboutToBeChanged.emit()
        self.txs.sort(key=lambda x: x[p_int], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

    def on_transactions_changed(self, transactions):
        self.beginResetModel()
        self.txs = transactions
        self.endResetModel()
