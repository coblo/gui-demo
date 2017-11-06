# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt
from PyQt5.QtWidgets import QTableView, QApplication, QAbstractItemView, QHeaderView

from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)


class CandidateModel(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderedDict()
        self.update_data()
        self.headers = ('Address', 'Skill', 'Start', 'End', 'Votes', 'Required', 'Grant')

    def update_data(self):
        client = get_active_rpc_client()
        perms_data = client.listpermissions()['result']
        old_keys = set(self.db.keys())
        new_keys = set()
        for data in perms_data:
            if not data['pending']:
                continue
            address = data['address']
            skill = data['type']
            for vote_round in data['pending']:
                start = vote_round['startblock']
                end = vote_round['endblock']
                votes = len(vote_round['admins'])
                required = vote_round['required']
                key = (address, skill, start, end)
                new_keys.add(key)
                self.db[key] = [address, skill, start, end, votes, required, 'Grant']
        deleted_keys = old_keys - new_keys
        for key in deleted_keys:
            del self.db[key]

    def headerData(self, col: int, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.db)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, idx: QModelIndex, role=None):
        if not idx.isValid():
            return None

        if role == Qt.DisplayRole:
            return self.db[list(self.db.keys())[idx.row()]][idx.column()]


class CandidateTableView(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = CandidateModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(600)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)


if __name__ == '__main__':
    import sys
    import app

    app.init()
    table_view_app = QApplication(sys.argv)
    table_view_win = CandidateTableView()
    table_view_win.show()
    sys.exit(table_view_app.exec())
