import logging
import webbrowser

from PyQt5.QtCore import QAbstractTableModel, Qt, QThread
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QWidget, QTableView

from app.backend.rpc import get_active_rpc_client
from app.signals import signals
from app.ui.token import Ui_WidgetToken

log = logging.getLogger(__name__)


class WidgetToken(QWidget, Ui_WidgetToken):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        table = TokenTableView(self)
        self.layout().insertWidget(0, table)


class TokensUpdater(QThread):
    UPDATE_INTERVALL = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        log.debug('init asset updater')

    @property
    def client(self):
        """Always use the rpc connection for the current profile"""
        return get_active_rpc_client()

    def run(self):
        client = get_active_rpc_client()

        while True:

            log.debug('check for new local token updates')
            try:
                # This triggers Network Info widget update that we always want
                blockchain_info = client.getblockchaininfo()
                # The node is downloading blocks if it has more headers than blocks
                if blockchain_info.blocks != blockchain_info.headers:
                    log.debug('blockchain syncing - skip expensive rpc calls')
                    self.sleep(self.UPDATE_INTERVALL)
                    continue
                wallet_tokens = client.getmultibalances()
            except Exception as e:
                log.exception('cannot get blocks via rpc: %s' % e)
                self.sleep(self.UPDATE_INTERVALL)
                continue
            tokens = []
            for token in wallet_tokens['total']:
                if 'name' not in token:
                    continue
                try:
                    token_info = client.listassets(token['name'], True)[0]
                except Exception as e:
                    log.debug(e)
                    continue
                if 'type' in token_info['details'] and token_info['details']['type'] == 'smart-license':
                    tokens.append([
                        token_info['details']['info'] if 'info' in token_info['details'] else '',
                        token['qty'],
                        token_info['issueqty'],
                        'No' if token_info['open'] else 'Yes',
                        token['name'] if 'name' in token else '',
                        token['assetref'] if 'assetref' in token else None
                    ])

            signals.wallet_tokens_changed.emit(tokens)

            self.sleep(self.UPDATE_INTERVALL)


class TokenTableView(QTableView):
    def __init__(self, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)

        self.table_model = TokenTableModel(self)
        self.setModel(self.table_model)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setFont(font)

        # Row height
        self.verticalHeader().setVisible(False)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setCornerButtonEnabled(True)

        self.clicked.connect(self.info_clicked)

        self.updater = TokensUpdater(self)
        self.updater.start()

    def info_clicked(self, index):
        if index.column() == self.table_model.NAME:
            db = self.table_model.tokens
            token = db[index.row()][self.table_model.ASSETREF]
            if token:
                link = 'https://explorer.coblo.net/token/'
                link += token
                webbrowser.open(link)


class TokenTableModel(QAbstractTableModel):

    DETAILS = 0
    AMOUNT = 1
    SUPPLY = 2
    LIMITED = 3
    NAME = 4
    ASSETREF = 5

    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.header = ['Info', 'Amount', 'Supply', 'Limited', 'TokenID']

        self.sort_index = 0
        self.sort_order = Qt.DescendingOrder

        self.tokens = []

        signals.wallet_tokens_changed.connect(self.tokens_changed)

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.tokens)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.header)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def data(self, index, role=Qt.DisplayRole):
        row, col = index.row(), index.column()
        token = self.tokens[row]
        if role == Qt.DisplayRole:
            if col == self.NAME:
                return token[col][:16] + '...'
            return token[col]

        if role == Qt.ToolTipRole:
            if col in [self.NAME, self.DETAILS]:
                return token[col]
            else:
                return None
        elif role == Qt.TextAlignmentRole and col in (self.AMOUNT, self.SUPPLY):
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.TextAlignmentRole and col == self.LIMITED:
            return QVariant(Qt.AlignCenter | Qt.AlignVCenter)
        elif role == Qt.ForegroundRole:
            if col == self.NAME:
                return QVariant(QColor(Qt.blue))
        elif role == Qt.FontRole and col in [self.AMOUNT, self.SUPPLY]:
            font = QFont("RobotoCondensed-Light", 9)
            return QVariant(font)
        elif role == Qt.FontRole and col == self.NAME:
            font = QFont("Roboto Light", 10)
            font.setUnderline(True)
            return QVariant(font)
        return None

    def sort(self, p_int, order=None):
        if p_int == self.DETAILS:
            self.layoutAboutToBeChanged.emit()
            self.layoutChanged.emit()
            return
        self.sort_index = p_int
        self.sort_order = order
        self.layoutAboutToBeChanged.emit()
        self.tokens.sort(key=lambda x: x[p_int], reverse=(order != Qt.DescendingOrder))
        self.layoutChanged.emit()

    def tokens_changed(self, tokens):
        self.tokens = tokens
        self.sort(self.sort_index, self.sort_order)