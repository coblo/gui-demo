import logging
import webbrowser
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, pyqtSignal, QThread, QModelIndex
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont, QCursor
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QWidget, QTableView

from app.backend.rpc import get_active_rpc_client
from app.signals import signals
from app.ui.wallet_history import Ui_widget_wallet_history

log = logging.getLogger(__name__)


class WalletHistory(QWidget, Ui_widget_wallet_history):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.table_wallet_history.setParent(None)
        table = TransactionTableView(self)
        self.layout_box_wallet_history.insertWidget(0, table)


class WalletTransactionsUpdater(QThread):
    UPDATE_INTERVALL = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug('init wallet transaction updater')

    @property
    def client(self):
        """Always use the rpc connection for the current profile"""
        return get_active_rpc_client()

    def run(self):
        synced_wallet_tx = ''
        synced_confirmed_wallet_tx = ''

        while True:

            log.debug('check for new local wallet updates')
            try:
                # This triggers Network Info widget update that we always want
                blockchain_info = self.client.getblockchaininfo()
                # The node is downloading blocks if it has more headers than blocks
                if blockchain_info.blocks != blockchain_info.headers:
                    log.debug('blockchain syncing - skip expensive rpc calls')
                    self.sleep(self.UPDATE_INTERVALL)
                    continue
                wallet_transactions = self.client.listwallettransactions(100)
                latest_tx_hash = ''
                if len(wallet_transactions) > 0:
                    latest_tx_hash = wallet_transactions[-1]["txid"]
                latest_confirmed_wallet_tx = ''
                for tx in reversed(wallet_transactions):
                    if tx.get("blocktime"):
                        latest_confirmed_wallet_tx = tx["txid"]
                        break
            except Exception as e:
                log.exception('cannot get blocks via rpc: %s' % e)
                self.sleep(self.UPDATE_INTERVALL)
                continue

            if latest_tx_hash != synced_wallet_tx or latest_confirmed_wallet_tx != synced_confirmed_wallet_tx:
                log.debug('syncing new wallet transactions')

                try:
                    balance_before = self.client.getbalance()
                    wallet_transactions = self.client.listwallettransactions(100, 0, False, True)
                    balance_after = self.client.getbalance()
                    if balance_before != balance_after:
                        log.debug("Balance changed while updating")
                        continue
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

        self.setHorizontalHeader(WalletHistoryHeader(Qt.Horizontal))
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setFont(font)
        header.on_enter.connect(self.reset_cursor)

        # Row height
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(40)

        self.setMouseTracking(True)
        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(True)
        self.clicked.connect(self.info_clicked)

        self.cursor_column = None
        self.updater = WalletTransactionsUpdater(self)
        self.updater.start()

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        column = self.columnAt(e.x())
        if self.cursor_column != column:
            if column == 5:
                self.setCursor(QCursor(Qt.PointingHandCursor))
            elif self.cursor_column == 5:
                self.setCursor(QCursor(Qt.ArrowCursor))
            self.cursor_column = column

    def reset_cursor(self):
        self.cursor_column = None
        self.setCursor(QCursor(Qt.ArrowCursor))

    def info_clicked(self, index):
        if index.column() == 5:
            db = self.table_model.txs
            txid = db[index.row()][self.table_model.INFO]
            link = 'https://explorer.coblo.net/tx/'
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

    PAYMENT = "payment"
    VOTE = "vote"
    MINING_REWARD = "mining_reward"
    PUBLISH = "publish"
    CREATE = "create"

    transaction_type_to_text = {
        PAYMENT: "Payment",
        VOTE: "Skill grant/revoke",
        MINING_REWARD: "Mining Reward",
        PUBLISH: "Publish"
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

        self.num_unconfirmed_raw = 0
        self.num_unconfirmed_processed = 0

        self.balance = 0
        self.raw_txs = []
        self.txs = []
        self.sort_index = self.DATETIME
        self.sort_order = Qt.AscendingOrder
        signals.wallet_transactions_changed.connect(self.wallet_transactions_changed)
        signals.balance_changed.connect(self.balance_changed)
        signals.profile_changed.connect(self.profile_changed)

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
                display = "{0:.8f}".format(amount)
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
            if col == self.TXTYPE and tx[col] in self.transaction_type_to_icon:
                return self.transaction_type_to_icon[tx[col]]
            elif col == self.INFO:
                return self.info_icon
        if role == Qt.ToolTipRole:
            if col == self.BALANCE:
                return '_' if tx[col] is None else "{0:n}".format(tx[col])
            elif col == self.TXTYPE and tx[col] in self.transaction_type_to_text:
                return self.transaction_type_to_text[tx[col]]
            elif col == self.COMMENT:
                return tx[col]
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
        if len(self.raw_txs) == 0:
            self.beginResetModel()
            self.raw_txs = transactions
            self.num_unconfirmed_processed = 0
            self.num_unconfirmed_raw = 0
            self.txs = self.process_wallet_transactions(transactions)
            self.endResetModel()
            self.sort(self.sort_index, self.sort_order)
        else:
            # handle unconfirmed
            if self.num_unconfirmed_raw > 0:
                self.beginRemoveRows(QModelIndex(), 0, self.num_unconfirmed_processed)
                self.raw_txs = self.raw_txs[:len(self.raw_txs)-self.num_unconfirmed_raw]
                self.txs = self.txs[self.num_unconfirmed_processed:]
                self.endRemoveRows()
            # insert new transactions
            latest_tx_id = ''
            if len(self.raw_txs) > 0:
                latest_tx_id = self.raw_txs[-1]["txid"]
            new_txs = []
            for tx in reversed(transactions):
                if tx["txid"] != latest_tx_id:
                    new_txs = [tx] + new_txs
                else:
                    break

            self.num_unconfirmed_processed = 0
            self.num_unconfirmed_raw = 0
            processed_txs = self.process_wallet_transactions(new_txs)
            self.beginInsertRows(QModelIndex(), 0, len(new_txs))
            self.raw_txs += new_txs
            self.txs = processed_txs + self.txs
            self.endInsertRows()

    def balance_changed(self, balance):
        self.balance = Decimal(balance).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

    def fetch_next_wallet_transactions(self):
        client = get_active_rpc_client()
        new_txs = []
        try:
            new_txs = client.listwallettransactions(100, len(self.raw_txs), False, True)
            if len(new_txs) < 100:
                self.wallet_transactions_left = False
        except Exception as e:
            log.debug(e)
        last_balance = self.txs[-1][self.BALANCE] if len(self.txs)>0 else self.balance
        processed_transactions = self.process_wallet_transactions(new_txs, last_balance)
        self.beginInsertRows(QModelIndex(), len(self.txs), len(self.txs)+len(processed_transactions))
        self.raw_txs = new_txs + self.raw_txs
        self.txs += processed_transactions
        self.endInsertRows()

    def profile_changed(self, profile):
        if profile.balance != self.balance:
            self.balance_changed(profile.balance)
            self.beginResetModel()
            self.num_unconfirmed_processed = 0
            self.num_unconfirmed_raw = 0
            self.txs = self.process_wallet_transactions(self.raw_txs)
            self.endResetModel()
            self.sort(self.sort_index, self.sort_order)

    def process_wallet_transactions(self, transactions, total_balance=None):
        processed_transactions = []
        sum_transaction_above = 0
        if total_balance is None:
            total_balance = self.balance
        for tx in reversed(transactions):
            if tx.get("valid") is False:
                continue
            txid = tx["txid"]
            amount = tx["balance"]["amount"]
            is_payment = True
            balance = Decimal(total_balance) - Decimal(sum_transaction_above)
            sum_transaction_above += amount
            unconfirmed = not tx.get("blocktime")
            if unconfirmed:
                self.num_unconfirmed_raw += 1
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
                if unconfirmed:
                    self.num_unconfirmed_processed += 1
            for item in tx["items"]:
                processed_transactions.append((
                    self.PUBLISH,
                    timestamp,
                    'Stream:"{}" , Keys: "{}"'.format(item['name'], "-".join(item['keys'])),
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))
                amount = 0
                is_payment = False
                if unconfirmed:
                    self.num_unconfirmed_processed += 1
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
                if unconfirmed:
                    self.num_unconfirmed_processed += 1
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
                if unconfirmed:
                    self.num_unconfirmed_processed += 1
            if is_payment:
                comment = ''
                if tx.get("comment"):
                    comment = tx.get("comment")
                elif tx.get("data"):
                    for data_item in tx.get("data"):
                        if "json" in data_item and "comment" in data_item["json"]:
                            comment = data_item["json"]["comment"]
                processed_transactions.append((
                    self.PAYMENT,
                    timestamp,
                    comment,
                    amount,
                    balance,
                    txid,
                    pos_in_block
                ))
                if unconfirmed:
                    self.num_unconfirmed_processed += 1

        return processed_transactions


class WalletHistoryHeader(QHeaderView):
    on_enter = pyqtSignal()

    def enterEvent(self, e):
        self.on_enter.emit()
