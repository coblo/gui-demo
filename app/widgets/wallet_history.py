from datetime import datetime
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt, pyqtSlot
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
        self.header = ['Date', 'Comment', 'Amount', 'Balance']
        self.txs = []
        self.insert_db_data(Transaction.select())
        self.sort_index = self.DATETIME
        self.sort_order = Qt.DescendingOrder
        self.sort(self.sort_index, self.sort_order)
        signals.listwallettransactions.connect(self.listwallettransactions)

    def insert_db_data(self, data):
        self.txs = self.txs + [self.tx_to_tuple(o) for o in data]

    def tx_to_tuple(self, tx) -> tuple:
        return (
            tx.datetime,
            tx.comment,
            tx.amount,
            tx.balance,
            tx.confirmations,
            tx.txid
        )

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
        self.sort_index = p_int
        self.sort_order = order
        self.layoutAboutToBeChanged.emit()
        if p_int == self.AMOUNT:
            self.txs.sort(key=lambda x: x[p_int].copy_abs(), reverse=(order != Qt.DescendingOrder))
        else:
            self.txs.sort(key=lambda x: x[p_int], reverse=(order != Qt.DescendingOrder))
        self.layoutChanged.emit()

    @pyqtSlot(list, list)
    def listwallettransactions(self, new_transactions, new_confirmations):
        # add new lines
        self.beginInsertRows(QModelIndex(), 0, len(new_transactions))
        self.insert_db_data(new_transactions)
        self.endInsertRows()

        # update confirmations column
        if len(new_confirmations) > 0:
            confirmations_map = {i.txid: i for i in new_confirmations}
            for index, tx_1 in enumerate(self.txs):
                if tx_1[self.TXID] in confirmations_map:
                    lst = list(self.txs[index])
                    lst[self.CONFIRMATIONS] = confirmations_map[tx_1[self.TXID]].confirmations
                    self.txs[index] = tuple(lst)
                    self.dataChanged.emit(self.index(index, self.CONFIRMATIONS), self.index(index, self.CONFIRMATIONS), [Qt.DisplayRole])
                    break

        self.sort(self.sort_index, self.sort_order)

