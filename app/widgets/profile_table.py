# -*- coding: utf-8 -*-
import logging

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSlot
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView, QPushButton, QStyledItemDelegate, QTableView

from app.models import Profile
from app.models.db import profile_session_scope
from app.widgets.profile_settings import ProfileSettingsDialog
from app.signals import signals


log = logging.getLogger(__name__)


class ProfileTableModel(QAbstractTableModel):

    def __init__(self, parent):
        super().__init__(parent)

        self.fields = ('Profile', 'Set Active', 'Edit Profile')
        self.profiles = []
        self.active_profile = None
        self.load_data()

        signals.profile_changed.connect(self.profiles_changed)
        # todo add button (vielleicht delete)

    def load_data(self):
        with profile_session_scope() as session:
            self.profiles = session.query(Profile.name).order_by(Profile.active.desc()).all()
            self.active_profile = Profile.get_active(session)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.fields[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.profiles)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.fields)

    def data(self, idx: QModelIndex, role=None):
        if role == Qt.TextAlignmentRole and idx.column() in (1, 2):
            return Qt.AlignCenter

        if not idx.isValid():
            return None

        profile_name = self.profiles[idx.row()][0]

        if role != Qt.DisplayRole:
            return None

        if idx.column() == 0:
            if profile_name == self.active_profile.name:
                return "{} (Active Profile)".format(profile_name)
            else:
                return "{}".format(profile_name)
        else:
            return None

    @pyqtSlot()
    def profiles_changed(self):
        self.beginResetModel()
        self.load_data()
        self.endResetModel()
        self.parent().create_table_buttons()


class ButtonEdit(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, idx):
        db = self.parent().table_model.profiles
        profile = db[idx.row()]
        btn = QPushButton('Edit Profile ✎', parent)
        btn.setStyleSheet(
            "QPushButton {background-color: #25B325; margin: 8 4 8 4; color: white; font-size: 8pt; width: 80px}")
        btn.setObjectName(profile[0])
        btn.clicked.connect(self.on_edit_clicked)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        return btn

    def on_edit_clicked(self):
        sender = self.sender()
        profile = sender.objectName()
        dialog = ProfileSettingsDialog(profile=profile)
        dialog.exec()


class ButtonSetActive(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, idx):
        db = self.parent().table_model.profiles
        profile = db[idx.row()]
        btn = QPushButton('Set Active', parent)
        btn.setStyleSheet(
            "QPushButton {background-color: #25B325; margin: 8 4 8 4; color: white; font-size: 8pt; width: 65px}")
        btn.setObjectName(profile[0])
        btn.clicked.connect(self.on_set_active_clicked)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        already_active = profile[0] == self.parent().table_model.active_profile.name
        if already_active:
            btn.setToolTip('Already Active')
            btn.setStyleSheet(
                "QPushButton {background-color: #aeaeae; margin: 8 4 8 4; color: white; font-size: 8pt; width: 65px}")
        btn.setDisabled(already_active)
        return btn

    def on_set_active_clicked(self):
        sender = self.sender()
        profile_name = sender.objectName()
        with profile_session_scope() as session:
            profile = session.query(Profile).filter(Profile.name == profile_name).first()
            profile.set_active(session)
            signals.profile_changed.emit()


class ProfileTableView(QTableView):
    def __init__(self, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)

        self.setMinimumWidth(400)

        self.table_model = ProfileTableModel(self)
        self.setModel(self.table_model)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.hide()

        # Row height
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(40)

        self.setFont(font)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(False)
        self.setCornerButtonEnabled(True)
        self.create_table_buttons()

    def create_table_buttons(self):
        self.setItemDelegateForColumn(1, ButtonEdit(self))
        for row in range(0, self.table_model.rowCount()):
            self.openPersistentEditor(self.table_model.index(row, 1))
        # TODO find a better way to fix button sizes collapsing on update
        w, h = self.size().width(), self.size().height()
        self.resize(w + 1, h)
        self.resize(w, h)
        self.setItemDelegateForColumn(2, ButtonSetActive(self))
        for row in range(0, self.table_model.rowCount()):
            self.openPersistentEditor(self.table_model.index(row, 2))
        w, h = self.size().width(), self.size().height()
        self.resize(w + 1, h)
        self.resize(w, h)
