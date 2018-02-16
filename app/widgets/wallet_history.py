import webbrowser
import logging

from PyQt5 import QtCore
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QWidget, QTableView

from app.ui.wallet_history import Ui_widget_wallet_history
from app.signals import signals
from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)

class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.table_wallet_history.setParent(None)
        table = TransactionTableView(self)
        self.layout_box_wallet_history.insertWidget(0, table)


class WalletTransactionsUpdater(QtCore.QThread):
    UPDATE_INTERVALL = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug('init wallet transaction updater')

    @property
    def client(self):
        """Always use the rpc connection for the current profile"""
        return get_active_rpc_client()

    def run(self):
        client = get_active_rpc_client()
        synced_wallet_tx = ''
        synced_confirmed_wallet_tx = ''

        while True:

            log.debug('check for new local wallet updates')
            try:
                # This triggers Network Info widget update that we always want
                blockchain_info = client.getblockchaininfo()['result']
                # The node is downloading blocks if it has more headers than blocks
                blockchain_downloading = blockchain_info['blocks'] != blockchain_info['headers']
                wallet_transactions = client.listwallettransactions(count=100)["result"]
                latest_tx_hash = wallet_transactions[99]["txid"]
                latest_confirmed_wallet_tx = ''
                for tx in reversed(wallet_transactions):
                    if tx.get("blocktime"):
                        latest_confirmed_wallet_tx = tx["txid"]
                        break
            except Exception as e:
                log.exception('cannot get blocks via rpc: %s' % e)
                self.sleep(self.UPDATE_INTERVALL)
                continue

            if blockchain_downloading:
                log.debug('blockchain syncing - skip expensive rpc calls')
                self.sleep(self.UPDATE_INTERVALL)
                continue

            if latest_tx_hash != synced_wallet_tx or latest_confirmed_wallet_tx != synced_confirmed_wallet_tx:
                log.debug('syncing new wallet transactions')

                try:
                    balance_before = client.getbalance()["result"]
                    wallet_transactions = client.listwallettransactions(count=100, verbose=True)["result"]
                    balance_after = client.getbalance()["result"]
                    if balance_before != balance_after:
                        log.debug("Balance changed while updating")
                        # todo: handle this
                    signals.balance_changed.emit(balance_before)
                    signals.wallet_transactions_changed.emit(wallet_transactions)

                except Exception as e:
                    log.exception(e)

                synced_wallet_tx = latest_tx_hash
                synced_confirmed_wallet_tx = latest_confirmed_wallet_tx

            self.sleep(self.UPDATE_INTERVALL)


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
        self.clicked.connect(self.info_clicked)

        self.updater = WalletTransactionsUpdater(self)
        self.updater.start()

    def info_clicked(self, index):
        if index.column() == 5:
            db = self.table_model.txs
            txid = db[index.row()][self.table_model.INFO]
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
    POS_IN_BLOCK = 6

    PAYMENT = "Payment",
    VOTE = "Skill grant/revoke",
    MINING_REWARD = "Mining Reward",
    PUBLISH = "Publish"

    transaction_types = {
        PAYMENT,
        VOTE,
        MINING_REWARD,
        PUBLISH
    }

    transaction_type_to_icon = {
        PAYMENT: QIcon(),
        VOTE: QIcon(),
        MINING_REWARD: QIcon(),
        PUBLISH: QIcon()
    }

    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.header = ['', 'Date', 'Comment', 'Amount', 'Balance', '']
        self.transaction_type_to_icon[self.PAYMENT].addPixmap(QPixmap(":/images/resources/money_black.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[self.VOTE].addPixmap(QPixmap(":/images/resources/vote_hammer_black.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[self.MINING_REWARD].addPixmap(QPixmap(":/images/resources/mining_reward.svg"), QIcon.Normal, QIcon.Off)
        self.transaction_type_to_icon[self.PUBLISH].addPixmap(QPixmap(":/images/resources/paper_plane_black.svg"), QIcon.Normal, QIcon.Off)

        self.info_icon = QIcon()
        self.info_icon.addPixmap(QPixmap(":/images/resources/info_circle.svg"), QIcon.Normal, QIcon.Off)

        self.wallet_transactions_left = True

        self.balance = 0
        self.raw_txs = []
        self.txs = []
        self.sort_index = self.DATETIME
        self.sort_order = Qt.AscendingOrder
        signals.wallet_transactions_changed.connect(self.wallet_transactions_changed)
        signals.balance_changed.connect(self.balance_changed)

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

        if role == Qt.DecorationRole:
            if col == self.TXTYPE and tx[col] in self.transaction_types:
                return self.transaction_type_to_icon[tx[col]]
            elif col == self.INFO:
                return self.info_icon
        if role == Qt.ToolTipRole:
            if col == self.BALANCE:
                return '_' if tx[col] is None else "{0:n}".format(tx[col])
            elif col == self.TXTYPE and tx[col] in self.transaction_types:
                return self.transaction_types[tx[col]]
            elif col == self.INFO:
                return self.info_icon
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

    def canFetchMore(self, index):
        return len(self.raw_txs) >= 100 and self.wallet_transactions_left

    def fetchMore(self, index):
        self.fetch_next_wallet_transactions()

    def sort(self, p_int, order=None):
        self.sort_index = p_int
        self.sort_order = order
        self.layoutAboutToBeChanged.emit()
        if p_int == self.DATETIME:
            self.txs.sort(key=lambda x: (datetime.now() if x[p_int] is None else x[p_int], 0-x[self.POS_IN_BLOCK]), reverse=(order != Qt.DescendingOrder))
        else:
            self.txs.sort(key=lambda x: x[p_int], reverse=(order != Qt.DescendingOrder))
        self.layoutChanged.emit()

    def wallet_transactions_changed(self, transactions):
        self.beginResetModel()
        self.raw_txs = transactions
        self.txs = self.process_wallet_transactions(transactions)
        self.endResetModel()
        self.sort(self.sort_index, self.sort_order)

    def balance_changed(self, balance):
        self.balance = Decimal(balance).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

    def fetch_next_wallet_transactions(self):
        client = get_active_rpc_client()
        new_txs = []
        try:
            new_txs = client.listwallettransactions(count=100, skip=len(self.raw_txs), verbose=True)["result"]
            if len(new_txs) < 100:
                self.wallet_transactions_left = False
        except Exception as e:
            log.debug(e)
        self.raw_txs = new_txs + self.raw_txs
        self.wallet_transactions_changed(self.raw_txs)

    def process_wallet_transactions(self, transactions):
        processed_transactions = []
        sum_transaction_above = 0
        for tx in reversed(transactions):
            if tx.get("valid") is False:
                continue
            txid = tx["txid"]
            amount = tx["balance"]["amount"]
            is_payment = True
            balance = Decimal(self.balance) - sum_transaction_above
            sum_transaction_above += amount
            timestamp = datetime.fromtimestamp(tx["blocktime"]) if tx.get("blocktime") else None
            pos_in_block = tx.get('blockindex', 0)
            if tx.get("generated"):
                processed_transactions.append((
                    self.MINING_REWARD,
                    timestamp,
                    '',
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))
                amount = 0
                is_payment = False
            for item in tx["items"]:
                processed_transactions.append((
                    self.PUBLISH,
                    timestamp,
                    'Stream:"' + item['name'] + '", Key: "' + item['key'] + '"',
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))
                amount = 0
                is_payment = False
            for perm in tx["permissions"]:
                processed_transactions.append((
                    self.VOTE,
                    timestamp,
                    '',
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))
                amount = 0
                is_payment = False
            if tx.get("create"):
                processed_transactions.append((
                    "Create",
                    timestamp,
                    'Type:"' + tx['create']['type'] + '", Name: "' + tx['create']['name'] + '"',
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))
                amount = 0
                is_payment = False
            if is_payment:
                processed_transactions.append((
                    self.PAYMENT,
                    timestamp,
                    '' if tx.get("comment") is None else tx.get("comment"),
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))

        return processed_transactions