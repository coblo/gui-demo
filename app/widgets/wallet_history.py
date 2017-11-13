from datetime import datetime
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHeaderView, QWidget
from decimal import Decimal, ROUND_DOWN

from app.models import Transaction
from app.ui.wallet_history import Ui_widget_wallet_history
from app.signals import signals


class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.table_model = TransactionHistoryTableModel(self)
        self.table_wallet_history.setModel(self.table_model)
        header = self.table_wallet_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)


class TransactionHistoryTableModel(QAbstractTableModel):

    DATETIME = 0
    COMMENT = 1
    AMOUNT = 2
    BALANCE = 3
    CONFIRMATIONS = 4
    TXID = 5

    def __init__(self, parent=None):
        super().__init__()
        signals.listwallettransactions.connect(self.listwallettransactions)
        self.header = ['Date', 'Comment', 'Amount', 'Balance']
        self.txs = self.get_db_data()

    def get_db_data(self):
        return [(
            o.datetime,
            o.comment,
            o.amount,
            o.balance,
            o.confirmations) for o in Transaction.select().order_by(Transaction.datetime.desc())]

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
                normalized = value.quantize(Decimal('.01'), rounding=ROUND_DOWN)
                display = "{0:n}".format(normalized)
                return '+' + display if value > 0 and col == self.AMOUNT else display
            elif isinstance(value, datetime):
                if tx[self.CONFIRMATIONS] == 0:
                    return 'Unconfirmed'
                else:
                    return value.strftime("%Y-%m-%d %H:%M")
            else:
                return str(value)
        if role == Qt.ToolTipRole and col in (self.AMOUNT, self.BALANCE):
            return "{0:n}".format(tx[col])
        elif role == Qt.TextAlignmentRole and col not in (self.COMMENT, self.DATETIME):
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.ForegroundRole:
            if col == self.AMOUNT and tx[self.AMOUNT] < 0:
                return QVariant(QColor(Qt.red))
        return None

    def sort(self, p_int, order=None):
        self.layoutAboutToBeChanged.emit()
        if p_int == self.AMOUNT:
            self.txs.sort(key=lambda x: x[p_int].copy_abs(), reverse=(order != Qt.DescendingOrder))
        else:
            self.txs.sort(key=lambda x: x[p_int], reverse=(order != Qt.DescendingOrder))
        self.layoutChanged.emit()

    @pyqtSlot()
    def listwallettransactions(self):
        self.beginResetModel()
        self.txs = self.get_db_data()
        self.endResetModel()
