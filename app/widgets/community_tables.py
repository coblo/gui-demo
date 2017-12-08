# -*- coding: utf-8 -*-
import sys
import logging
import math

import timeago
from datetime import datetime, timedelta

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSlot
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import QApplication, QHeaderView, QMessageBox, QWidget, QMenu, QAbstractItemView, QPushButton, \
    QStyledItemDelegate, QTableView

from app import enums
from app.backend.rpc import get_active_rpc_client
from app.models import Alias
from app.models import Permission, Profile, PendingVote, Block, Vote
from app.signals import signals

from peewee import fn

from app import ADMIN_CONSENUS_MINE, ADMIN_CONSENUS_ADMIN

log = logging.getLogger(__name__)


class PermissionModel(QAbstractTableModel):
    # TODO: make permissions table model sortable (keep sort order on data update)

    def __init__(self, parent, perm_type=enums.MINE):
        super().__init__(parent)

        self.last_24_h_mine_count = self.get_24_hour_mine_count()
        self.last_24_h_vote_count = self.get_24_hour_vote_count()

        self._fields = (
            'Alias', 'Address', 'Last Mined' if perm_type == enums.MINE else 'Last Voted', 'Last 24h', 'Revokes',
            'Action')
        self._perm_type = perm_type
        self._data = self.load_data()
        self._alias_list = self.load_alias_list()

        signals.permissions_changed.connect(self.permissions_changed)

        if perm_type == enums.ADMIN:
            # Update guardians table if votes have changed
            signals.votes_changed.connect(self.permissions_changed)

    def load_data(self):
        if self._perm_type == enums.MINE:
            return list(Permission.validators())
        elif self._perm_type == enums.ADMIN:
            return list(Permission.guardians())

    def load_alias_list(self):
        return Alias.get_aliases()

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
            # if self._perm_type == enums.MINE: todo
            #     last_mined = perm_obj.address.get_last_mined()
            #     if last_mined:
            #         return timeago.format(last_mined, datetime.now())
            # if self._perm_type == enums.ADMIN:
            #     last_voted = perm_obj.address.get_last_voted()
            #     if last_voted:
            #         return timeago.format(last_voted, datetime.now())
            return 'Never'
        if idx.column() == 3:
            if self._perm_type == enums.MINE: # todo
                return "{} Blocks".format(self.last_24_h_mine_count[
                                              perm_obj.address] if perm_obj.address in self.last_24_h_mine_count else 0)
            else:
                return "{} Votes".format(self.last_24_h_vote_count[
                                             perm_obj.address] if perm_obj.address in self.last_24_h_vote_count else 0)
        if idx.column() == 4:
            # if self._perm_type == enums.MINE: # todo
            #     return "{} of {}".format(perm_obj.address.num_validator_revokes(),
            #                              math.ceil(Permission.num_guardians() * ADMIN_CONSENUS_MINE))
            # else:
            #     return "{} of {}".format(perm_obj.address.num_guardian_revokes(),
            #                              math.ceil(Permission.num_guardians() * ADMIN_CONSENUS_ADMIN))
            return 'TODO revoked'

    def flags(self, idx: QModelIndex):
        if idx.column() == 1:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super().flags(idx)

    def get_24_hour_mine_count(self):
        # return {b.miner.address: b.block_count for b in Block.select( #todo
        #     Block.miner,
        #     fn.COUNT(Block.hash).alias("block_count")
        # ).where(datetime.now() - timedelta(days=1) <= Block.time).group_by(Block.miner)}
        return []

    def get_24_hour_vote_count(self):
        # return {v.from_address.address: v.vote_count for v in Vote.select( todo
        #     Vote.from_address,
        #     fn.COUNT(Vote.txid).alias("vote_count")
        # ).where(datetime.now() - timedelta(days=1) <= Vote.time).group_by(Vote.from_address)}
        return []

    @pyqtSlot()
    def permissions_changed(self):
        self.last_24_h_mine_count = self.get_24_hour_mine_count()
        self.last_24_h_vote_count = self.get_24_hour_vote_count()

        self.beginResetModel()
        self._data = self.load_data()
        self.endResetModel()
        self.parent().create_table_buttons()


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)
        self.already_voted = []
        signals.permissions_changed.connect(self.permissions_changed)
        self.permissions_changed()

    def permissions_changed(self):
        # own_votes = PendingVote.select().where( todo
        #     PendingVote.start_block == PendingVote.end_block == 0,
        #     PendingVote.given_from == Profile.get_active().address
        # )
        own_votes = []
        for vote in own_votes:
            self.already_voted.append({
                'address': vote.address.address,
                'perm_type': vote.perm_type
            })

    def createEditor(self, parent, option, idx):
        btn = QPushButton('Revoke', parent)
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
                    sender.setStyleSheet(
                        "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 70px}")
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
            self.profile = Profile.get_active()

        signals.is_admin_changed.connect(self.is_admin_changed)

        # self.pressed.connect(self.on_cell_clicked)

        self.table_model = PermissionModel(self, perm_type=self.perm_type)
        self.setModel(self.table_model)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        self.setColumnHidden(5, not self.profile.is_admin)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
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
        self.create_table_buttons()

    def create_table_buttons(self):
        self.setItemDelegateForColumn(5, ButtonDelegate(self))
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

