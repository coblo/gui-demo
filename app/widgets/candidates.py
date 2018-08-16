# -*- coding: utf-8 -*-
import logging
from functools import partial
import math

from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt, pyqtSlot, QThread
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtWidgets import QTableView, QApplication, QAbstractItemView, QHeaderView, QWidget, QMessageBox, QMenu, \
    QPushButton, QStyledItemDelegate

from app import enums
from app.models import Alias
from app.models import Profile, PendingVote, Permission
from app.models.db import data_session_scope, profile_session_scope
from app.signals import signals
from app import ADMIN_CONSENUS_ADMIN, ADMIN_CONSENUS_MINE

from app.backend.rpc import get_active_rpc_client

log = logging.getLogger(__name__)
MAX_END_BLOCK = 4294967295


class CandidateModelUpdater(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def run(self):
        with data_session_scope() as session:
            self.parent().candidates = PendingVote.get_candidates(session)
            self.parent().aliases = Alias.get_aliases(session)
            self.parent().already_granted = PendingVote.already_granted(session)
            self.parent().num_guardians = Permission.num_guardians(session)


class CandidateModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.candidates = []
        self.aliases = []
        self.already_granted = []
        self.num_guardians = 0
        self.update_thread = CandidateModelUpdater(self)
        self.update_thread.finished.connect(self.update_finished)
        self.update_thread.start()
        self.headers = ('Alias', 'Address', 'Skill', 'Grants', 'Action')

        signals.votes_changed.connect(self.votes_changed)
        signals.permissions_changed.connect(self.update_num_guardians)

    def update_num_guardians(self):
        with data_session_scope() as session:
            self.num_guardians = Permission.num_guardians(session)

    def flags(self, idx: QModelIndex):
        if idx.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(idx)

    def headerData(self, col: int, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.candidates)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, idx: QModelIndex, role=None):
        row = idx.row()
        col = idx.column()
        candidate = self.candidates[row]
        if not idx.isValid():
            return None

        if role == Qt.TextAlignmentRole and col in (3, 4):
            return Qt.AlignCenter

        if role == Qt.EditRole and col == 1:
            return candidate.address_to

        if role == Qt.DisplayRole:
            if col == 0:
                return self.aliases[candidate.address_to] if candidate.address_to in self.aliases else None
            elif col == 1:
                return candidate.address_to
            elif idx.column() == 2:
                return 'guardian' if candidate.perm_type.name == enums.ADMIN else 'validator'
            elif idx.column() == 3:
                return "{} of {}".format(
                    candidate.grants,
                    math.ceil(self.num_guardians * (ADMIN_CONSENUS_ADMIN if candidate.perm_type.name == enums.ADMIN else ADMIN_CONSENUS_MINE))
                )
            elif idx.column() == 4:
                for vote in self.already_granted:
                    if vote.address_to == candidate.address_to and vote.perm_type == candidate.perm_type:
                        return True
                return False

    @pyqtSlot()
    def votes_changed(self):
        self.beginResetModel()
        self.update_thread.start()

    @pyqtSlot()
    def update_finished(self):
        self.endResetModel()
        self.parent().create_table_buttons()


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)
        self.balance_is_zero = True
        signals.on_balance_status_changed.connect(self.on_balance_status_changed)

    def on_balance_status_changed(self, balance_is_zero):
        self.balance_is_zero = balance_is_zero

    def createEditor(self, parent, option, idx):
        db = self.parent().table_model.candidates
        candidate = db[idx.row()]
        btn = QPushButton('Grant', parent)
        btn.setStyleSheet(
            "QPushButton {background-color: #0183ea; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        btn.setObjectName(candidate.address_to)
        btn.clicked.connect(partial(self.on_grant_clicked, candidate.perm_type.name))
        already_voted = False
        for vote in self.parent().table_model.already_granted:
            if vote.address_to == candidate.address_to and vote.perm_type == candidate.perm_type:
                already_voted = True
        if already_voted:
            btn.setStyleSheet(
                "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        else:
            btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setDisabled(already_voted or self.balance_is_zero)
        if self.balance_is_zero:
            btn.setToolTip("You need coins to vote.")
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
                client.grant(address, skill)
                sender.setDisabled(True)
                sender.setStyleSheet(
                    "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
                signals.new_unconfirmed.emit('vote')
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

        with profile_session_scope() as session:
            self.setColumnHidden(4, not Profile.get_active(session).is_admin)

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

        signals.is_admin_changed.connect(self.is_admin_changed)

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

    @pyqtSlot(bool)
    def is_admin_changed(self, is_admin):
        self.setColumnHidden(4, not is_admin)


if __name__ == '__main__':
    import sys
    import app

    app.init()
    table_view_app = QApplication(sys.argv)
    table_view_win = CandidateTableView()
    table_view_win.show()
    sys.exit(table_view_app.exec())
