from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt5.QtWidgets import QHeaderView, QWidget
from decimal import Decimal, ROUND_DOWN
from app.ui.wallet_addresses import Ui_widget_addresses


class WalletAddresses(QWidget, Ui_widget_addresses):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.updater = parent.updater
        self.table_model = AddressesTableModel(self)
        self.table_wallet_history.setModel(self.table_model)
        header = self.table_wallet_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)


class AddressesTableModel(QAbstractTableModel):

    ADDRESS = 0
    BALANCE = 1

    def __init__(self, parent=None):
        super().__init__()
        self.updater = parent.updater
        self.updater.addresses_changed.connect(self.on_addresses_changed)
        self.header = ['Address', 'Balance']
        self.addresses = []

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.addresses)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.header)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def data(self, index, role=Qt.DisplayRole):
        row, col = index.row(), index.column()
        address = self.addresses[row]
        if role == Qt.DisplayRole:
            value = address[self.header[col]]
            if isinstance(value, Decimal):
                normalized = value.quantize(Decimal('.01'), rounding=ROUND_DOWN)
                display = "{0:n}".format(normalized)
                return display
            else:
                return str(value)
        if role == Qt.ToolTipRole and col == self.BALANCE:
            return "{0:n}".format(address[col])
        elif role == Qt.TextAlignmentRole and col == self.BALANCE:
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def sort(self, p_int, order=None):
        self.layoutAboutToBeChanged.emit()
        self.addresses.sort(key=lambda x: x[p_int], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

    def on_addresses_changed(self, addresses):
        self.beginResetModel()
        self.addresses = addresses
        self.endResetModel()
