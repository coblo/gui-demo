# -*- coding: utf-8 -*-
import logging
from functools import partial
import math
from collections import OrderedDict

from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt, pyqtSlot
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtWidgets import QTableView, QApplication, QAbstractItemView, QHeaderView, QWidget, QMessageBox, QMenu, \
    QPushButton, QStyledItemDelegate

from app.models import Profile, Address, CurrentVote, Permission
from app.signals import signals
from app import ADMIN_CONSENUS_ADMIN, ADMIN_CONSENUS_MINE

from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)
MAX_END_BLOCK = 4294967295


class CandidateModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderedDict()
        self.update_data()
        self.headers = ('Alias', 'Address', 'Skill', 'Grants', 'Action')

        signals.votes_changed.connect(self.votes_changed)

    def update_data(self):
        old_keys = set(self.db.keys())
        new_keys = set()
        for candidate in CurrentVote.get_candidates():
            try:
                alias = Address.select().where(Address.address == candidate.address).first().alias
            except AttributeError:
                alias = 'unknown'
            if candidate.start_block == 0 and candidate.end_block == MAX_END_BLOCK:
                vote_count = CurrentVote.select().where(
                    CurrentVote.address == candidate.address,
                    CurrentVote.start_block == 0,
                    CurrentVote.end_block == MAX_END_BLOCK).count()
                already_voted = CurrentVote.select().where(
                    CurrentVote.address == candidate.address,
                    CurrentVote.start_block == 0,
                    CurrentVote.end_block == MAX_END_BLOCK,
                    CurrentVote.given_from == Profile.get_active().address).count() > 0
                if candidate.perm_type == Permission.ADMIN:
                    required = math.ceil(Permission.num_guardians() * ADMIN_CONSENUS_ADMIN)
                else:
                    required = math.ceil(Permission.num_guardians() * ADMIN_CONSENUS_MINE)
                key = (candidate.address, candidate.perm_type)
                new_keys.add(key)
                self.db[key] = [alias, candidate.address.address, candidate.perm_type,
                                "{} of {}".format(vote_count, required), already_voted]
        deleted_keys = old_keys - new_keys
        for key in deleted_keys:
            del self.db[key]

    def flags(self, idx: QModelIndex):
        if idx.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(idx)

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

        if role == Qt.TextAlignmentRole and idx.column() in (3, 4):
            return Qt.AlignCenter

        if role == Qt.EditRole and idx.column() in (1, 4):
            return self.db[list(self.db.keys())[idx.row()]][1]

        if role == Qt.DisplayRole:
            return self.db[list(self.db.keys())[idx.row()]][idx.column()]

    @pyqtSlot()
    def votes_changed(self):
        self.beginResetModel()
        self.update_data()
        self.endResetModel()
        self.parent().create_table_buttons()


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, idx):
        db = self.parent().table_model.db
        db_entry = db[list(db.keys())[idx.row()]]
        btn = QPushButton('Grant', parent)
        btn.setStyleSheet(
            "QPushButton {background-color: #0183ea; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        btn.setObjectName(db_entry[1])
        btn.clicked.connect(partial(self.on_grant_clicked, db_entry[2]))
        if db_entry[4]:
            btn.setStyleSheet(
                "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
            btn.setDisabled(db_entry[4])
        else:
            btn.setCursor(QCursor(Qt.PointingHandCursor))
        return btn

    def on_grant_clicked(self, skill):
        sender = self.sender()
        address = sender.objectName()
        skill_name = skill
        if skill == 'admin':
            skill_name = 'guardian'
        elif skill == 'mine':
            skill_name = 'validator'
        message_box = QMessageBox()
        answer = message_box.question(QWidget(), "Grant Skills",
                                      "Are you sure you want to grant {} skills to {}?".format(skill_name, address),
                                      message_box.Yes | message_box.No)

        if answer == message_box.Yes:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            client = get_active_rpc_client()
            try:
                response = client.grant(address, skill)
                if response['error'] is not None:
                    err_msg = response['error']['message']
                    raise RuntimeError(err_msg)
                else:
                    sender.setDisabled(True)
                    sender.setStyleSheet(
                        "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
                QApplication.restoreOverrideCursor()
            except Exception as e:
                err_msg = str(e)
                error_dialog = QMessageBox()
                error_dialog.setWindowTitle('Error while granting')
                error_dialog.setText(err_msg)
                error_dialog.setIcon(QMessageBox.Warning)
                QApplication.restoreOverrideCursor()
                error_dialog.exec_()


class CandidateTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = CandidateModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

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

        self.setColumnHidden(4, not Profile.get_active().is_admin)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        # TODO implement candidates table sorting
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openCustomMenu)
        self.create_table_buttons()

    def create_table_buttons(self):
        self.setItemDelegateForColumn(4, ButtonDelegate(self))
        for row in range(0, self.table_model.rowCount()):
            self.openPersistentEditor(self.table_model.index(row, 4))
        # TODO find a better way to fix button sizes collapsing on update
        w, h = self.size().width(), self.size().height()
        self.resize(w + 1, h)
        self.resize(w, h)

    def openCustomMenu(self, QPoint):
        menu = QMenu(self)
        copy_address = menu.addAction("Copy Address")
        copy_alias = menu.addAction("Copy Alias")
        row = self.rowAt(QPoint.y())
        action = menu.exec_(self.mapToGlobal(QPoint))
        if action == copy_address:
            index = self.table_model.index(row, 1)
            QApplication.clipboard().setText(self.table_model.itemData(index)[0])
        elif action == copy_alias:
            index = self.table_model.index(row, 0)
            QApplication.clipboard().setText(self.table_model.itemData(index)[0])


if __name__ == '__main__':
    import sys
    import app

    app.init()
    table_view_app = QApplication(sys.argv)
    table_view_win = CandidateTableView()
    table_view_win.show()
    sys.exit(table_view_app.exec())
