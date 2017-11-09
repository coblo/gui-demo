# -*- coding: utf-8 -*-
import logging
from PyQt5 import QtGui

from PyQt5 import QtWidgets
from collections import OrderedDict

from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt
from PyQt5.QtWidgets import QTableView, QApplication, QAbstractItemView, QHeaderView

from app.signals import signals
from app.models import Address

from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)
MAX_END_BLOCK = 4294967295

class CandidateModel(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderedDict()
        self.update_data()
        self.headers = ('Alias', 'Address', 'Skill', 'Grants', 'Action')

        signals.votes_changed.connect(self.update_data)

    def update_data(self):
        client = get_active_rpc_client()
        perms_data = client.listpermissions()['result']
        old_keys = set(self.db.keys())
        new_keys = set()
        for data in perms_data:
            if not data['pending']:
                continue
            address = data['address']
            alias = Address.select().where(Address.address==address).first().alias
            skill = data['type']
            for vote_round in data['pending']:
                if vote_round['startblock'] == 0 and vote_round['endblock'] == MAX_END_BLOCK:
                    votes = len(vote_round['admins'])
                    required = vote_round['required']
                    key = (address, skill)
                    new_keys.add(key)
                    self.db[key] = [alias, address, skill, "{} of {}".format(votes, votes + required), '']
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


class ButtonDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):
        QtWidgets.QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, idx):
        btn = QtWidgets.QPushButton('Grant', parent)
        btn.setStyleSheet("QPushButton {background-color: #0183ea; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        address = idx.data(Qt.EditRole)
        btn.setObjectName(address)
        btn.clicked.connect(self.on_grant_clicked)
        return btn

    def on_grant_clicked(self):
        sender = self.sender()
        address = sender.objectName()
        # skill = self.parent().skill todo: find skill
        log.debug('TODO: grant %s for %s' % ('todo', address))
        # client = get_active_rpc_client()
        # response = client.revoke(address, perm_type)

class CandidateTableView(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = CandidateModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)

        font = QtGui.QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setFont(font)

        # Row height
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(40)

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setCornerButtonEnabled(True)
        self.create_table_buttons()


    def create_table_buttons(self):
        self.setItemDelegateForColumn(4, ButtonDelegate(self))
        for row in range(0, self.table_model.rowCount()):
            self.openPersistentEditor(self.table_model.index(row, 4))

if __name__ == '__main__':
    import sys
    import app

    app.init()
    table_view_app = QApplication(sys.argv)
    table_view_win = CandidateTableView()
    table_view_win.show()
    sys.exit(table_view_app.exec())
