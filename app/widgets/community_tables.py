# -*- coding: utf-8 -*-
import sys
import logging
import timeago
from datetime import datetime
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSlot
from PyQt5.QtWidgets import QHeaderView
from app.models import Permission
from app.settings import settings
from app.signals import signals


log = logging.getLogger(__name__)


class PermissionModel(QAbstractTableModel):

    # TODO: make permissions table model sortable (keep sort order on data update)

    def __init__(self, parent, perm_type=Permission.MINE):
        super().__init__(parent)

        self._fields = ('Alias', 'Address', 'Last Active', 'Revokes', 'Action')
        self._perm_type = perm_type
        self._data = self.load_data()

        signals.listpermissions.connect(self.listpermissions)

    def load_data(self):
        if self._perm_type == Permission.MINE:
            return list(Permission.validators())
        elif self._perm_type == Permission.ADMIN:
            return list(Permission.guardians())

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._fields[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._data)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self._fields)

    def data(self, idx: QModelIndex, role=None):

        if role == Qt.TextAlignmentRole and idx.column() in (3, 4):
            return Qt.AlignCenter

        if not idx.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        perm_obj = self._data[idx.row()]

        if idx.column() == 0:
            return perm_obj.address.alias
        if idx.column() == 1:
            return perm_obj.address_id
        if idx.column() == 2:
            if self._perm_type == Permission.MINE:
                last_mined = perm_obj.address.last_mined()
                if last_mined:
                    return timeago.format(last_mined, datetime.now())
            return 'Go find out'
        if idx.column() == 3:
            if self._perm_type == Permission.MINE:
                return "{} of {}".format(perm_obj.address.num_validator_revokes(), Permission.num_guardians())
            else:
                return "{} of {}".format(perm_obj.address.num_guardian_revokes(), Permission.num_guardians())

    @pyqtSlot()
    def listpermissions(self):
        self.beginResetModel()
        self._data = self.load_data()
        self.endResetModel()
        self.parent().create_table_buttons()


class ButtonDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):
        QtWidgets.QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QtWidgets.QPushButton('Revoke', parent)
        combo.setStyleSheet(
            "QPushButton {background-color: red; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}"
        )
        combo.clicked.connect(self.currentIndexChanged)
        return combo

    def setEditorData(self, editor, index):
        log.debug('triggered ButtonDelegate setEditorData')
        editor.blockSignals(True)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        log.debug('triggered ButtonDelegate setModelData')

    @pyqtSlot()
    def currentIndexChanged(self):
        log.debug('triggered ButtonDelegate currentIndexChanged')


class CommunityTableView(QtWidgets.QTableView):

    # TODO: show number of "blocks mined"/"votes given" in last 24h in validator/guardian tables

    def __init__(self, *args, **kwargs):
        perm_type = kwargs.pop('perm_type')
        QtWidgets.QTableView.__init__(self, *args, **kwargs)

        signals.admin_state_changed.connect(self.admin_state_changed)

        self.table_model = PermissionModel(self, perm_type=perm_type)
        self.setModel(self.table_model)

        font = QtGui.QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        self.setColumnHidden(4, not settings.value('is_admin'))

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

    def admin_state_changed(self, new_admin_state):
        self.setColumnHidden(4, not new_admin_state)

if __name__ == '__main__':
    from app.models import init_profile_db, init_data_db
    # from app.tools.runner import run_widget
    init_profile_db()
    init_data_db()
    app = QtWidgets.QApplication(sys.argv)
    win = CommunityTableView(perm_type=Permission.MINE)
    win.show()
    sys.exit(app.exec_())
