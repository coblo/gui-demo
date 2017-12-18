# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QWidget

from app.ui.iscc import Ui_Widget_ISCC

log = logging.getLogger(__name__)


class WidgetISCC(QWidget, Ui_Widget_ISCC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        # Connections
        self.btn_search_iscc.clicked.connect(self.search_iscc)
        self.btn_register.clicked.connect(self.register)

        self.table_iscc.setParent(None)
        table_iscc = ISCCTableView(self)
        self.tab_search.layout().insertWidget(1, table_iscc)

    def search_iscc(self):
        pass

    def register(self):
        pass

class ISCCModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.isccs = []
        self.aliases = []
        self.update_data()
        self.headers = ('ISCC', 'Title', 'Date', 'Publisher')

        # signals.votes_changed.connect(self.votes_changed)
        # signals.permissions_changed.connect(self.update_num_guardians)

    def update_data(self):
        self.isccs = [{
            'iscc': 'GRP33BK272VUD-W51K85H57OKUD-L988YUL4R1NJD-MEPU8D3L2T5ZT',
            'title': 'Title',
            'date': datetime.now(),
            'publisher': 'Publisher'
        }]

    def flags(self, idx: QModelIndex):
        if idx.column() == 0:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(idx)

    def headerData(self, col: int, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.isccs)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, idx: QModelIndex, role=None):
        row = idx.row()
        col = idx.column()
        iscc = self.isccs[row]
        if not idx.isValid():
            return None

        if role == Qt.EditRole and col == 0:
            return iscc['iscc']

        if role == Qt.DisplayRole:
            if col == 0:
                # return self.aliases[candidate.address_to]
                return iscc['iscc']
            elif col == 1:
                return iscc['title']
            elif idx.column() == 2:
                return "{}".format(iscc['date'])
            elif idx.column() == 3:
                return iscc['publisher']


class ISCCTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = ISCCModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setFont(font)

        self.setWordWrap(False)

        # Row height
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(40)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        # TODO implement iscc tables sorting
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openCustomMenu)

    def openCustomMenu(self, QPoint):
        menu = QMenu(self)
        copy_iscc = menu.addAction("Copy ISCC")
        row = self.rowAt(QPoint.y())
        action = menu.exec_(self.mapToGlobal(QPoint))
        if action == copy_iscc:
            index = self.table_model.index(row, 0)
            QApplication.clipboard().setText(self.table_model.itemData(index)[0])
