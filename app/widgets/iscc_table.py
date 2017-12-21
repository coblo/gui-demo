# -*- coding: utf-8 -*-
import logging

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QMenu, QTableView

from app.models import Alias, ISCC
from app.models.db import data_session_scope
from app.signals import signals

log = logging.getLogger(__name__)


class ISCCModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.isccs = []
        self.aliases = []
        self.update_data()
        self.headers = ('ISCC', 'Title', 'Date', 'Publisher')
        signals.iscc_inserted.connect(self.update_data)

    def update_data(self, search_term=None):
        self.beginResetModel()
        with data_session_scope() as session:
            self.aliases = Alias.get_aliases(session)
            if search_term:
                self.isccs = ISCC.filter_iscc(session, search_term)
            else:
                self.isccs = ISCC.get_all_iscc(session)
        self.endResetModel()

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
        iscc_code = iscc.ISCC.meta_id + '-' + iscc.ISCC.content_id + '-' + iscc.ISCC.data_id + '-' + iscc.ISCC.instance_id
        if not idx.isValid():
            return None

        if role == Qt.EditRole and col == 0:
            return iscc_code

        if role == Qt.DisplayRole:
            if col == 0:
                return iscc_code
            elif col == 1:
                return iscc.ISCC.title
            elif idx.column() == 2:
                return "{}".format(iscc.mining_time)
            elif idx.column() == 3:
                return self.aliases[iscc.ISCC.address]


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
