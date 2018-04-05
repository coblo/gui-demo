# -*- coding: utf-8 -*-
import logging

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from app.models import Alias
from app.models.db import data_session_scope

log = logging.getLogger(__name__)


class ConflictModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conflicts = []
        self.aliases = []
        self.iscc = None
        self.headers = ('Meta ID', 'Content ID', 'Data ID', 'Instance ID', 'Title', 'Publisher')

    def update_data(self, conflicts, iscc):
        self.beginResetModel()
        with data_session_scope() as session:
            self.aliases = Alias.get_aliases(session)
            self.conflicts = conflicts
            self.iscc = iscc.split('-')
        self.endResetModel()

    def headerData(self, col: int, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.conflicts)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, idx: QModelIndex, role=None):
        row = idx.row()
        col = idx.column()
        conflict = self.conflicts[row]

        if not idx.isValid():
            return None

        if role == Qt.DisplayRole:
            if col == 0:
                return conflict.meta_id
            elif col == 1:
                return conflict.content_id
            elif col == 2:
                return conflict.data_id
            elif col == 3:
                return conflict.instance_id
            elif col == 4:
                return conflict.title
            elif col == 5:
                return self.aliases[conflict.address] if conflict.address in self.aliases else conflict.address

        elif role == Qt.ForegroundRole:
            if col == 0 and conflict.meta_id == self.iscc[0]:
                return QVariant(QColor(Qt.red))
            if col == 1 and conflict.content_id == self.iscc[1]:
                return QVariant(QColor(Qt.red))
            if col == 2 and conflict.data_id == self.iscc[2]:
                return QVariant(QColor(Qt.red))
            if col == 3 and conflict.instance_id == self.iscc[3]:
                return QVariant(QColor(Qt.red))

        elif role == Qt.FontRole and col in [0, 1, 2, 3]:
            font = QFont("RobotoCondensed-Light", 8)
            return QVariant(font)


class ConflictTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = ConflictModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)

        font = QFont()
        font.setFamily("Roboto Condensed Light")
        font.setPointSize(9)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
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
