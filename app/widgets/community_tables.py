# -*- coding: utf-8 -*-
import sys
import logging
import math

import timeago
from datetime import datetime

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSlot
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import QApplication, QHeaderView, QMessageBox, QWidget, QMenu, QAbstractItemView, QPushButton, \
    QStyledItemDelegate, QTableView

from app import enums
from app.backend.rpc import get_active_rpc_client
from app.models import Alias, MiningReward, Permission, Profile, PendingVote, Vote
from app.models.db import data_session_scope, profile_session_scope
from app.signals import signals

from app import ADMIN_CONSENUS_MINE, ADMIN_CONSENUS_ADMIN

log = logging.getLogger(__name__)


class PermissionModel(QAbstractTableModel):
    # TODO: make permissions table model sortable (keep sort order on data update)

    def __init__(self, parent, perm_type=enums.MINE):
        super().__init__(parent)

        self.last_24_h_mine_count = {}
        self.last_24_h_vote_count = {}
        self.last_mined = {}
        self.last_voted = {}
        self.count_revokes = {}
        self.num_guardians = 0

        self._fields = (
            'Alias', 'Address', 'Last Mined' if perm_type == enums.MINE else 'Last Voted', 'Last 24h', 'Revokes',
            'Action')
        self._perm_type = perm_type
        self._data = []
        self._alias_list = []
        self.already_revoked = []
        self.load_data()

        signals.permissions_changed.connect(self.permissions_changed)
        signals.votes_changed.connect(self.permissions_changed)
        signals.alias_list_changed.connect(self.alias_list_changed)
        self.fill_count_lists()

    def load_data(self):
        with data_session_scope() as session:
            if self._perm_type == enums.MINE:
                self._data = list(Permission.validators(session))
            elif self._perm_type == enums.ADMIN:
                self._data = list(Permission.guardians(session))
            self._alias_list = Alias.get_aliases(session)
        self.already_revoked = PendingVote.already_revoked(session, self._perm_type)

    def fill_count_lists(self):
        with data_session_scope() as session:
            for reward in MiningReward.mined_last_24h(session):
                self.last_24_h_mine_count[reward.address] = reward.count
            for reward in MiningReward.last_mined(session):
                self.last_mined[reward.address] = reward.last_mined
            for vote in Vote.voted_last_24h(session):
                self.last_24_h_vote_count[vote.from_address] = vote.count
            for vote in Vote.last_voted(session):
                self.last_voted[vote.from_address] = vote.last_voted
            for pending_vote in PendingVote.num_revokes(session, self._perm_type):
                self.count_revokes[pending_vote.address_to] = pending_vote.count

            self.num_guardians = Permission.num_guardians(session)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._fields[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._data)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self._fields)

    def data(self, idx: QModelIndex, role=None):

        if role == Qt.TextAlignmentRole and idx.column() in (3, 4, 5):
            return Qt.AlignCenter

        if not idx.isValid():
            return None

        perm_obj = self._data[idx.row()]

        if role == Qt.EditRole and idx.column() in (1, 5):
            return perm_obj.address

        if role != Qt.DisplayRole:
            return None

        if idx.column() == 0:
            if self._alias_list and perm_obj.address in self._alias_list.keys():
                return self._alias_list[perm_obj.address]
            return ''
        if idx.column() == 1:
            return perm_obj.address
        if idx.column() == 2:
            if self._perm_type == enums.MINE:
                if perm_obj.address in self.last_mined:
                    return timeago.format(self.last_mined[perm_obj.address], datetime.now())
            if self._perm_type == enums.ADMIN:
                if perm_obj.address in self.last_voted:
                    return timeago.format(self.last_voted[perm_obj.address], datetime.now())
            return 'Never'
        if idx.column() == 3:
            if self._perm_type == enums.MINE:
                return "{} Blocks".format(self.last_24_h_mine_count[
                                              perm_obj.address] if perm_obj.address in self.last_24_h_mine_count else 0)
            else:
                return "{} Votes".format(self.last_24_h_vote_count[
                                             perm_obj.address] if perm_obj.address in self.last_24_h_vote_count else 0)
        if idx.column() == 4:
            return "{} of {}".format(self.count_revokes[perm_obj.address] if perm_obj.address in self.count_revokes else 0,
                                     math.ceil(self.num_guardians * ADMIN_CONSENUS_ADMIN if self._perm_type == enums.ADMIN else ADMIN_CONSENUS_MINE))

    def flags(self, idx: QModelIndex):
        if idx.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(idx)

    def alias_list_changed(self):
        self.beginResetModel()
        with data_session_scope() as session:
            self._alias_list = Alias.get_aliases(session)
        self.endResetModel()

    @pyqtSlot()
    def permissions_changed(self):
        self.fill_count_lists()
        self.beginResetModel()
        self.load_data()
        self.endResetModel()
        self.parent().create_table_buttons(self.parent().balance_is_zero)


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent, balance_is_zero):
        QStyledItemDelegate.__init__(self, parent)
        self.balance_is_zero = balance_is_zero

    def createEditor(self, parent, option, idx):
        db = self.parent().table_model._data
        table_entry = db[idx.row()]
        already_voted = False
        for vote in self.parent().table_model.already_revoked:
            if vote.address_to == table_entry.address and self.parent().table_model._perm_type == table_entry.perm_type.name:
                already_voted = True
        btn = QPushButton('Revoke', parent)
        btn.setStyleSheet(
            "QPushButton {background-color: #0183ea; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        address = idx.data(Qt.EditRole)
        btn.setObjectName(address)
        btn.clicked.connect(self.on_revoke_clicked)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        if already_voted or self.balance_is_zero:
            btn.setStyleSheet(
                "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
        btn.setDisabled(already_voted or self.balance_is_zero)
        if self.balance_is_zero:
            btn.setToolTip("You need coins to vote.")
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
                client.revoke(address, perm_type)
                sender.setDisabled(True)
                sender.setStyleSheet(
                    "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
                signals.new_unconfirmed.emit('vote')
                QApplication.restoreOverrideCursor()
            except Exception as e:
                err_msg = str(e)
                error_dialog = QMessageBox()
                error_dialog.setWindowTitle('Error while revoking')
                error_dialog.setText(err_msg)
                error_dialog.setIcon(QMessageBox.Warning)
                QApplication.restoreOverrideCursor()
                error_dialog.exec_()


class CommunityTableView(QTableView):
    def __init__(self, *args, **kwargs):
        self.perm_type = kwargs.pop('perm_type')
        QTableView.__init__(self, *args, **kwargs)

        self.setMinimumWidth(400)
        try:
            self.profile = self.parent().profile
        except AttributeError:
            # In case of standalone usage
            with profile_session_scope() as session:
                self.profile = Profile.get_active(session)

        signals.is_admin_changed.connect(self.is_admin_changed)

        # self.pressed.connect(self.on_cell_clicked)

        self.table_model = PermissionModel(self, perm_type=self.perm_type)
        self.setModel(self.table_model)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        self.setColumnHidden(5, not self.profile.is_admin)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setFont(font)

        # Row height
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(40)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        # TODO implement comminity tables sorting
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openCustomMenu)
        self.balance_is_zero = True
        self.create_table_buttons(self.balance_is_zero)
        signals.on_balance_status_changed.connect(self.on_balance_status_changed)

    def on_balance_status_changed(self, balance_is_zero):
        if balance_is_zero != self.balance_is_zero:
            self.table_model.beginResetModel()
            self.balance_is_zero = balance_is_zero
            self.table_model.endResetModel()
            self.create_table_buttons(balance_is_zero)

    def create_table_buttons(self, balance_is_zero):
        self.setItemDelegateForColumn(5, ButtonDelegate(self, balance_is_zero))
        for row in range(0, self.table_model.rowCount()):
            self.openPersistentEditor(self.table_model.index(row, 5))
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
        self.setColumnHidden(5, not is_admin)
