# -*- coding: utf-8 -*-
import logging

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QMenu, QTableView

from app.models import Alias, ISCC
from app.models.db import data_session_scope
from app.signals import signals

log = logging.getLogger(__name__)

class ISCCModelUpdater(QThread):
    def __init__(self, search_term, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aliases = []
        self.isccs = []
        self.search_term = search_term

    def run(self):
        with data_session_scope() as session:
            self.aliases = Alias.get_aliases(session)
            if self.search_term:
                self.isccs = ISCC.filter_iscc(session, self.search_term, page = 0, page_size = 1000)
            else:
                self.isccs = ISCC.get_all_iscc_paged(session, page = 0, page_size = 1000)


class ISCCModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.isccs = []
        self.aliases = []
        self.updateWorker = None
        self.requires_update = False
        self.search_term = None
        self.headers = ('ISCC', 'Title', 'Date', 'Publisher')
        self.update_data()
        signals.iscc_inserted.connect(self.update_data)

    def update_data(self, search_term=None):
        self.search_term = search_term
        if self.updateWorker and self.updateWorker.isRunning():
            self.requires_update = True
        else:
            self.updateWorker = ISCCModelUpdater(self.search_term)
            self.updateWorker.finished.connect(self.updater_finished)
            self.requires_update = False
            self.updateWorker.start()

    def updater_finished(self):
        # Update Model
        if self.aliases != self.updateWorker.aliases or self.isccs != self.updateWorker.isccs:
            self.beginResetModel()
            self.aliases = self.updateWorker.aliases
            self.isccs = self.updateWorker.isccs
            self.endResetModel()

        # Data has been modified in the meantime.. Update again
        if self.requires_update:
            self.requires_update = False
            self.updateWorker = ISCCModelUpdater(self.search_term)
            self.updateWorker.start()

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
                address = iscc.ISCC.address
                return self.aliases[address] if address in self.aliases else "{}".format(address)


class ISCCTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = ISCCModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
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
