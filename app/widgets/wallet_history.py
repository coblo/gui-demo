import webbrowser
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont, QCursor
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QWidget, QPushButton, QStyledItemDelegate, QTableView

from app.models import WalletTransaction
from app.ui.wallet_history import Ui_widget_wallet_history
from app.signals import signals


class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.table_wallet_history.setParent(None)
        table = TransactionTableView(self)
        self.layout_box_wallet_history.insertWidget(0, table)


class TransactionTableView(QTableView):
    def __init__(self, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)

        self.table_model = TransactionHistoryTableModel(self)
        self.setModel(self.table_model)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setFont(font)

        # Row height
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(40)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(True)
        self.create_table_buttons()

    def create_table_buttons(self):
        self.setItemDelegateForColumn(5, ButtonDelegate(self))
        for row in range(0, self.table_model.rowCount()):
            self.openPersistentEditor(self.table_model.index(row, 5))
        # TODO find a better way to fix button sizes collapsing on update
        w, h = self.size().width(), self.size().height()
        self.resize(w + 1, h)
        self.resize(w, h)


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)
        self.info_icon = QIcon()
        self.info_icon.addPixmap(
            QPixmap(":/images/resources/info_circle.svg"),
            QIcon.Normal,
            QIcon.Off
        )

    def createEditor(self, parent, option, idx):
        db = self.parent().table_model.txs
        table_entry = db[idx.row()]
        btn = QPushButton('', parent)
        btn.setIcon(self.info_icon)
        btn.setStyleSheet(
            "QPushButton {margin: 8 4 8 4; border: none;}")
        btn.setObjectName(table_entry.txid)
        btn.clicked.connect(self.on_revoke_clicked)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        return btn

    def on_revoke_clicked(self):
        sender = self.sender()
        txid = sender.objectName()
        link = 'https://explorer.content-blockchain.org/Content%20Blockchain%20Project%20(Testnet)/tx/'
        link += txid
        webbrowser.open(link)

class TransactionHistoryTableModel(QAbstractTableModel):

    TXTYPE = 0
    DATETIME = 1
    COMMENT = 2
    AMOUNT = 3
    BALANCE = 4
    INFO = 5

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
        self.header = ['', 'Date', 'Comment', 'Amount', 'Balance', '']
        self.transaction_type_to_icon[WalletTransaction.PAYMENT].addPixmap(QPixmap(":/images/resources/money_black.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[WalletTransaction.VOTE].addPixmap(QPixmap(":/images/resources/vote_hammer_black.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[WalletTransaction.MINING_REWARD].addPixmap(QPixmap(":/images/resources/mining_reward.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[WalletTransaction.PUBLISH].addPixmap(QPixmap(":/images/resources/paper_plane_black.svg"), QIcon.Normal, QIcon.Off)

        self.txs = None
        self.sort_index = self.DATETIME
        self.sort_order = Qt.AscendingOrder
        self.refreshData()
        signals.wallet_transactions_changed.connect(self.refreshData)

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
            if col == self.DATETIME:
                return 'unconfirmed' if tx[col] is None else "{}".format(tx[col])
            if col == self.AMOUNT:
                amount = tx[col]
                if amount == 0:
                    amount = 0
                display = "{0:n}".format(amount)
                return '+' + display if amount > 0 else display
            if col == self.BALANCE:
                if tx[col] is None:
                    return '-'
                normalized = tx[col].quantize(Decimal('.01'), rounding=ROUND_DOWN)
                display = "{0:n}".format(normalized)
                return display
            if col == self.TXTYPE:
                return None
            if col == self.INFO:
                return None
            return tx[col]

        if role == Qt.DecorationRole and col == self.TXTYPE and tx[col] in self.transaction_types:
            return self.transaction_type_to_icon[tx[col]]
        if role == Qt.ToolTipRole:
            if col == self.BALANCE:
                return '_' if tx[col] is None else "{0:n}".format(tx[col])
            elif col == self.TXTYPE and tx[col] in self.transaction_types:
                return self.transaction_types[tx[col]]
            else:
                return None
        elif role == Qt.TextAlignmentRole and col not in (self.COMMENT, self.DATETIME):
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.ForegroundRole:
            if col == self.AMOUNT and tx[col] < 0:
                return QVariant(QColor(Qt.red))
        elif role == Qt.FontRole and col == self.AMOUNT:
            font = QFont("RobotoCondensed-Light", 9)
            return QVariant(font)
        return None

    def sort(self, p_int, order=None):
        self.sort_index = p_int
        self.sort_order = order
        self.layoutAboutToBeChanged.emit()
        if p_int == self.DATETIME:
            self.txs.sort(key=lambda x: (datetime.now() if x[p_int] is None else x[p_int]), reverse=(order != Qt.DescendingOrder))
        else:
            self.txs.sort(key=lambda x: x[p_int], reverse=(order != Qt.DescendingOrder))
        self.layoutChanged.emit()


    def refreshData(self):
        from app.models.db import data_session_scope
        self.beginResetModel()
        with data_session_scope() as session:
            self.txs = WalletTransaction.get_wallet_history(session)
        self.endResetModel()
        self.sort(self.sort_index, self.sort_order)
