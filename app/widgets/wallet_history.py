from datetime import datetime
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt, pyqtSlot
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QHeaderView, QWidget
from decimal import Decimal, ROUND_DOWN

from app.models import WalletTransaction
from app.ui.wallet_history import Ui_widget_wallet_history
from app.signals import signals

class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.table_model = TransactionHistoryTableModel(self)
        self.table_wallet_history.setModel(self.table_model)
        self.table_wallet_history.horizontalHeader().setSortIndicator(1, Qt.AscendingOrder)
        header = self.table_wallet_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)


class TransactionHistoryTableModel(QAbstractTableModel):

    TXTYPE = 0
    DATETIME = 1
    COMMENT = 2
    AMOUNT = 3
    BALANCE = 4

    transaction_types = {
        WalletTransaction.PAYMENT: "Payment",
        WalletTransaction.VOTE: "Skill grant/revoke",
        WalletTransaction.MINING_REWARD: "Mining Reward",
        WalletTransaction.PUBLISH: "Publish"
    }

    transaction_type_to_icon = {
        WalletTransaction.PAYMENT: QIcon(),
        WalletTransaction.VOTE: QIcon(),
        WalletTransaction.MINING_REWARD: QIcon(),
        WalletTransaction.PUBLISH: QIcon()
    }

    def __init__(self, parent=None):
        super().__init__()
        self.header = ['', 'Date', 'Comment', 'Amount', 'Balance']
        self.transaction_type_to_icon[WalletTransaction.PAYMENT].addPixmap(QPixmap(":/images/resources/money_black.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[WalletTransaction.VOTE].addPixmap(QPixmap(":/images/resources/vote_hammer_black.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[WalletTransaction.MINING_REWARD].addPixmap(QPixmap(":/images/resources/mining_reward.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[WalletTransaction.PUBLISH].addPixmap(QPixmap(":/images/resources/paper_plane_black.svg"), QIcon.Normal, QIcon.Off)

        self.txs = WalletTransaction.get_wallet_history()
        # self.insert_db_data(MyTransaction.select()) todo
        self.sort_index = self.DATETIME
        self.sort_order = Qt.AscendingOrder
        self.sort(self.sort_index, self.sort_order)
        signals.wallet_transaction_inserted.connect(self.add_new_transaction)
        signals.wallet_transaction_updated.connect(self.update_transaction)

    def insert_db_data(self, data):
        self.txs = self.txs + [data]

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
            if col == self.TXTYPE:
                return ''
            if col == self.DATETIME:
                return 'unconfirmed' if tx['time'] is None else "{}".format(tx['time'])
            if col == self.COMMENT:
                return tx['comment']
            if col == self.AMOUNT:
                amount = tx['amount']
                if amount == 0:
                    amount = 0
                display = "{0:n}".format(amount)
                return '+' + display if amount > 0 else display
            if col == self.BALANCE:
                if tx['balance'] is None:
                    return '-'
                normalized = tx['balance'].quantize(Decimal('.01'), rounding=ROUND_DOWN)
                display = "{0:n}".format(normalized)
                return display
        if role == Qt.DecorationRole and col == self.TXTYPE and tx['tx_type'] in self.transaction_types:
            return self.transaction_type_to_icon[tx['tx_type']]
        if role == Qt.ToolTipRole:
            if col == self.BALANCE:
                return '_' if tx['balance'] is None else "{0:n}".format(tx['balance'])
            elif col == self.TXTYPE and tx['tx_type'] in self.transaction_types:
                return self.transaction_types[tx['tx_type']]
            else:
                return None
        elif role == Qt.TextAlignmentRole and col not in (self.COMMENT, self.DATETIME):
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.TextAlignmentRole and col == self.TXTYPE and tx['tx_type'] in self.transaction_types:
            return self.transaction_type_to_icon[tx['tx_type']].actualSize()
        elif role == Qt.ForegroundRole:
            if col == self.AMOUNT and tx['amount'] < 0:
                return QVariant(QColor(Qt.red))
        elif role == Qt.FontRole and col == self.AMOUNT:
            font = QFont("RobotoCondensed-Light", 9)
            return QVariant(font)
        return None

    def sort(self, p_int, order=None):
        self.sort_index = p_int
        self.sort_order = order
        self.layoutAboutToBeChanged.emit()
        if p_int == self.AMOUNT:
            self.txs.sort(key=lambda x: x['amount'].copy_abs(), reverse=(order != Qt.DescendingOrder))
        elif p_int == self.BALANCE:
            self.txs.sort(key=lambda x: x['balance'], reverse=(order != Qt.DescendingOrder))
        elif p_int == self.DATETIME:
            self.txs.sort(key=lambda x: (datetime.now() if x['time'] is None else x['time']), reverse=(order != Qt.DescendingOrder))
        elif p_int == self.COMMENT:
            self.txs.sort(key=lambda x: x['comment'], reverse=(order != Qt.DescendingOrder))
        elif p_int == self.TXTYPE:
            self.txs.sort(key=lambda x: x['tx_type'], reverse=(order != Qt.DescendingOrder))
        self.layoutChanged.emit()

    @pyqtSlot(object)
    def add_new_transaction(self, new_transactions):
        # add new lines
        self.beginInsertRows(QModelIndex(), 0, 1)
        self.insert_db_data(new_transactions)
        self.endInsertRows()

        self.sort(self.sort_index, self.sort_order)

    @pyqtSlot(object)
    def update_transaction(self, new_transactions):
        # update confirmations column
        for index, tx_1 in enumerate(self.txs):
            if tx_1['txid'] == new_transactions['txid']:
                self.txs[index] = new_transactions
                self.dataChanged.emit(self.index(index, self.DATETIME), self.index(index, self.DATETIME), [Qt.DisplayRole])
                self.dataChanged.emit(self.index(index, self.BALANCE), self.index(index, self.BALANCE), [Qt.DisplayRole])

        self.sort(self.sort_index, self.sort_order)
