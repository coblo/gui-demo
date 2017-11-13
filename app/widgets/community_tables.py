# -*- coding: utf-8 -*-
import sys
import logging
import math

import timeago
from datetime import datetime
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSlot
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication, QHeaderView, QMessageBox, QWidget

from app.backend.rpc import get_active_rpc_client
from app.models import Permission, Profile
from app.signals import signals

from app import ADMIN_CONSENUS_MINE, ADMIN_CONSENUS_ADMIN

log = logging.getLogger(__name__)


class PermissionModel(QAbstractTableModel):
    # TODO: make permissions table model sortable (keep sort order on data update)

    def __init__(self, parent, perm_type=Permission.MINE):
        super().__init__(parent)

        self._fields = ('Alias', 'Address', 'Last Mined' if perm_type==Permission.MINE else 'Last Voted', 'Revokes', 'Action')
        self._perm_type = perm_type
        self._data = self.load_data()

        signals.listpermissions.connect(self.listpermissions)

        if perm_type == Permission.ADMIN:
            # Update guardians table if votes have changed
            signals.votes_changed.connect(self.listpermissions)

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

        perm_obj = self._data[idx.row()]

        if role == Qt.EditRole and idx.column() in (1, 4):
            return perm_obj.address_id

        if role != Qt.DisplayRole:
            return None

        if idx.column() == 0:
            return perm_obj.address.alias
        if idx.column() == 1:
            return perm_obj.address_id
        if idx.column() == 2:
            if self._perm_type == Permission.MINE:
                last_mined = perm_obj.address.get_last_mined()
                if last_mined:
                    return timeago.format(last_mined, datetime.now())
            if self._perm_type == Permission.ADMIN:
                last_voted = perm_obj.address.get_last_voted()
                if last_voted:
                    return timeago.format(last_voted, datetime.now())
            return 'Never'
        if idx.column() == 3:
            if self._perm_type == Permission.MINE:
                return "{} of {}".format(perm_obj.address.num_validator_revokes(), math.ceil(Permission.num_guardians() * ADMIN_CONSENUS_MINE))
            else:
                return "{} of {}".format(perm_obj.address.num_guardian_revokes(), math.ceil(Permission.num_guardians() * ADMIN_CONSENUS_ADMIN))

    def flags(self, idx: QModelIndex):
        if idx.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(idx)

    @pyqtSlot()
    def listpermissions(self):
        self.beginResetModel()
        self._data = self.load_data()
        self.endResetModel()
        self.parent().create_table_buttons()


class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        QtWidgets.QStyledItemDelegate.__init__(self, parent)
        self.already_voted = []
        signals.listpermissions.connect(self.listpermissions)
        self.listpermissions()

    def listpermissions(self):
        # TODO try to avoid this api call by storing/getting needed info from database
        client = get_active_rpc_client()
        try:
            perms_data = client.listpermissions()['result']
            for perm in perms_data:
                for pending in perm['pending']:
                    if pending['startblock'] == 0 and pending['endblock'] == 0:
                        if Profile.get_active().address in pending['admins'] and perm['address'] not in self.already_voted:
                            self.already_voted.append({
                                'address': perm['address'],
                                'perm_type': perm['type']
                            })
        except Exception:
            log.debug('could not get permission data via rpc')
            return

    def createEditor(self, parent, option, idx):
        btn = QtWidgets.QPushButton('Revoke', parent)
        btn.setStyleSheet(
            "QPushButton {background-color: #0183ea; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        address = idx.data(Qt.EditRole)
        btn.setObjectName(address)
        btn.clicked.connect(self.on_revoke_clicked)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        for vote in self.already_voted:
            if vote['address'] == address and vote['perm_type'] == self.parent().perm_type:
                btn.setDisabled(True)
                btn.setStyleSheet(
                    "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        return btn

    def on_revoke_clicked(self):
        sender = self.sender()
        address = sender.objectName()
        perm_type = self.parent().perm_type
        skill_name = perm_type
        if perm_type == 'admin':
            skill_name = 'guardian'
        elif perm_type == 'mine':
            skill_name = 'validator'
        message_box = QMessageBox()
        answer = message_box.question(QWidget(), "Revoke Skills",
                                      "Are you sure you want to revoke {} skills from {}?".format(skill_name, address),
                                      message_box.Yes | message_box.No)
        if answer == message_box.Yes:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            client = get_active_rpc_client()
            try:
                response = client.revoke(address, perm_type)
                if response['error'] is not None:
                    err_msg = response['error']['message']
                    raise RuntimeError(err_msg)
                else:
                    sender.setDisabled(True)
                    sender.setStyleSheet("QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
                QApplication.restoreOverrideCursor()
            except Exception as e:
                err_msg = str(e)
                error_dialog = QMessageBox()
                error_dialog.setWindowTitle('Error while revoking')
                error_dialog.setText(err_msg)
                error_dialog.setIcon(QMessageBox.Warning)
                QApplication.restoreOverrideCursor()
                error_dialog.exec_()


class CommunityTableView(QtWidgets.QTableView):
    # TODO: show number of "blocks mined"/"votes given" in last 24h in validator/guardian tables

    def __init__(self, *args, **kwargs):
        self.perm_type = kwargs.pop('perm_type')
        QtWidgets.QTableView.__init__(self, *args, **kwargs)

        self.setMinimumWidth(400)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        try:
            self.profile = self.parent().profile
        except AttributeError:
            # In case of standalone usage
            self.profile = Profile.get_active()

        signals.is_admin_changed.connect(self.is_admin_changed)

        # self.pressed.connect(self.on_cell_clicked)

        self.table_model = PermissionModel(self, perm_type=self.perm_type)
        self.setModel(self.table_model)

        font = QtGui.QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        self.setColumnHidden(4, not self.profile.is_admin)

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

    @pyqtSlot(bool)
    def is_admin_changed(self, is_admin):
        self.setColumnHidden(4, not is_admin)


if __name__ == '__main__':
    from app.models import init_profile_db, init_data_db
    from app.helpers import init_logging

    init_logging()
    # from app.tools.runner import run_widget
    init_profile_db()
    init_data_db()
    app = QtWidgets.QApplication(sys.argv)
    win = CommunityTableView(perm_type=Permission.MINE)
    win.show()
    sys.exit(app.exec_())
