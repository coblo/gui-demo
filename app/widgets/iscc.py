# -*- coding: utf-8 -*-
import base64
import logging
import os
from binascii import hexlify
import qrcode
import ubjson

from PyQt5.QtCore import QAbstractTableModel, pyqtSlot, QDir, QEvent, QMimeData, QModelIndex, QObject, QUrl, Qt
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QDragLeaveEvent, QDropEvent, QFont, QPixmap, QDragEnterEvent
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QFileDialog, QHeaderView, QMenu, QTableView, QWidget
from PyQt5.QtWidgets import QMessageBox

from app.backend.rpc import get_active_rpc_client
from app.models import Alias
from app.models.db import data_session_scope
from app.ui.iscc import Ui_Widget_ISCC
from app.models import ISCC
from app.tools import iscc as iscc_lib

log = logging.getLogger(__name__)


class WidgetISCC(QWidget, Ui_Widget_ISCC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self.meta_id = None
        self.content_id = None
        self.data_id = None
        self.instance_id = None
        self.iscc = None
        self.conflict_in_meta = False

        # Intercept drag & drop events from button
        self.button_dropzone.installEventFilter(self)

        # Connections
        self.button_dropzone.clicked.connect(self.file_select_dialog)
        self.btn_search_iscc.clicked.connect(self.search_iscc)
        self.edit_search_iscc.returnPressed.connect(self.search_iscc)
        self.btn_register.clicked.connect(self.register)
        self.edit_title.textChanged.connect(self.title_changed)
        self.edit_extra.textChanged.connect(self.extra_changed)

        self.table_iscc.setParent(None)
        self.table_iscc = ISCCTableView(self)
        self.tab_search.layout().insertWidget(1, self.table_iscc)

        self.widget_generated_iscc.setHidden(True)
        self.label_title_conflicts.setHidden(True)
        self.table_conflicts.setParent(None)
        self.table_conflicts = ConflictTableView(self)
        self.table_conflicts.setHidden(True)
        self.tab_register.layout().insertWidget(4, self.table_conflicts)
        self.label_title_extra.setHidden(True)
        self.widget_extra.setHidden(True)

    def search_iscc(self):  # todo: wenn man einen ganzen iscc sucht findet man nichts...
        search_term = self.edit_search_iscc.text()
        self.table_iscc.model().update_data(search_term)

    def register(self):
        # todo subscribe
        client = get_active_rpc_client()
        data = dict(title=self.edit_title.text())
        serialized = ubjson.dumpb(data)
        data_hex = hexlify(serialized).decode('utf-8')
        error = None
        try:
            response = client.publish('testiscc', self.iscc, data_hex)
            if response['error'] is not None:
                error = response['error']
        except Exception as e:
            error = e
        if error is None:
            self.edit_title.clear()
            self.label_qr.clear()
            self.label_iscc.clear()
            self.meta_id = None
            self.content_id = None
            self.data_id = None
            self.instance_id = None
            self.iscc = None
            self.widget_generated_iscc.setHidden(True)
            self.button_dropzone.setText('Drop your image or text file here or click to choose.')
        else:
            QMessageBox.warning(QMessageBox(), 'Error while publishing', str(error), QMessageBox.Close,
                                QMessageBox.Close)

    def title_changed(self, title):
        extra = ''
        if self.conflict_in_meta:
            extra = self.edit_extra.text()
        if extra:
            self.meta_id = iscc_lib.generate_meta_id(title=title, extra=extra)
        else:
            self.meta_id = iscc_lib.generate_meta_id(title=title)
        if self.content_id:
            self.show_conflicts()

    def extra_changed(self, extra):
        self.meta_id = iscc_lib.generate_meta_id(title=self.edit_title.text(), extra=extra)
        if self.content_id:
            self.show_conflicts()

    def process_file(self, file_path):
        self.button_dropzone.setText(file_path)
        with open(file_path, 'rb') as infile:
            self.instance_id = iscc_lib.generate_instance_id(infile)
        if file_path.split('.')[-1] in ['jpg', 'png', 'jpeg']:
            self.content_id = iscc_lib.generate_image_hash(file_path)
        else:
            self.content_id = base64.b32encode(b'\x10' +  os.urandom(7)).rstrip(b'=').decode('ascii') # todo
        with open(file_path, 'rb') as infile:
            self.data_id = iscc_lib.generate_data_id(infile)
        if self.meta_id:
            self.show_conflicts()

    @pyqtSlot()
    def file_select_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', QDir().homePath())
        if file_path:
            self.process_file(file_path)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.DragEnter:
            log.debug('DragEnter')
            self.on_drag_enter(obj, event)
        elif event.type() == QEvent.DragLeave:
            log.debug('DragLeave')
            self.on_drag_leave(obj, event)
        elif event.type() == QEvent.Drop:
            log.debug('Drop')
            self.on_drop(obj, event)
        return QWidget.eventFilter(self, obj, event)

    def on_drag_enter(self, obj: QObject, event: QDragEnterEvent):
        mimedata = event.mimeData()
        assert isinstance(mimedata, QMimeData)

        if mimedata.hasUrls():
            if len(mimedata.urls()) > 1:
                return self.reject_drag(event, 'One file at a time please. Try again!')
            url = mimedata.urls()[0]
            assert isinstance(url, QUrl)

            if not url.isValid():
                return self.reject_drag(event, 'Invalid URL. Try again!')
            if not url.isLocalFile():
                return self.reject_drag(event, 'Only local files are supported. Try again!')
            if os.path.isdir(url.toLocalFile()):
                return self.reject_drag(event, 'Directories not supported. Try again!')

            event.accept()
            self.button_dropzone.setStyleSheet(
                'QPushButton:enabled {background-color: #0183ea; color: white;}'
            )
            self.button_dropzone.setText('Just drop it :)')

    def on_drag_leave(self, obj: QObject, event: QDragLeaveEvent):
        self.button_dropzone.setText('Drop your image or text file here or click to choose.')
        self.button_dropzone.style().polish(self.button_dropzone)

    def on_drop(self, obj: QObject, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.process_file(file_path)

    def show_conflicts(self):
        self.widget_generated_iscc.setHidden(False)
        self.iscc = self.meta_id + '-' + self.content_id + '-' + self.data_id + '-' + self.instance_id
        self.label_iscc.setText(self.iscc)
        img = qrcode.make(self.meta_id + self.content_id + self.data_id + self.instance_id)
        img.save('tmp.png')
        pixmap = QPixmap('tmp.png')
        pixmap = pixmap.scaledToWidth(128)
        pixmap = pixmap.scaledToHeight(128)
        self.label_qr.setPixmap(pixmap)
        with data_session_scope() as session:
            self.btn_register.setDisabled(
                ISCC.already_exists(session, self.meta_id, self.content_id, self.data_id, self.instance_id))
            conflicts = ISCC.get_conflicts(session, self.meta_id, self.content_id, self.data_id, self.instance_id)
            if len(conflicts) > 0:
                self.label_title_conflicts.setHidden(False)
                self.table_conflicts.setHidden(False)
                self.table_conflicts.model().update_data(conflicts, self.iscc)
                if ISCC.conflict_in_meta(session, self.meta_id):
                    self.widget_extra.setHidden(False)
                    self.conflict_in_meta = True
            else:
                self.label_title_conflicts.setHidden(True)
                self.table_conflicts.setHidden(True)
            self.label_title_extra.setHidden(not self.conflict_in_meta)

class ISCCModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.isccs = []
        self.aliases = []
        self.update_data()
        self.headers = ('ISCC', 'Title', 'Date', 'Publisher')

    def update_data(self, search_term=None):
        self.beginResetModel()
        with data_session_scope() as session:
            self.aliases = Alias.get_aliases(session)
            if search_term:
                self.isccs = ISCC.filter_iscc(session, search_term)
            else:
                self.isccs = ISCC.get_all_iscc(session)
        self.endResetModel()

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
                return "{}".format(iscc.time)
            elif idx.column() == 3:
                return self.aliases[iscc.ISCC.address]


class ISCCTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = ISCCModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
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

class ConflictModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conflicts = []
        self.aliases = []
        self.iscc = None
        self.headers = ('Meta ID', 'Content ID', 'Data ID', 'Instance ID', 'Title', 'Publisher')

    def update_data(self, conflicts, iscc):
        self.beginResetModel()
        with data_session_scope() as session:
            self.aliases = Alias.get_aliases(session)
            self.conflicts = conflicts
            self.iscc = iscc.split('-')
        self.endResetModel()

    def headerData(self, col: int, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[col]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.conflicts)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, idx: QModelIndex, role=None):
        row = idx.row()
        col = idx.column()
        conflict = self.conflicts[row]

        if not idx.isValid():
            return None

        if role == Qt.DisplayRole:
            if col == 0:
                return conflict.meta_id
            elif col == 1:
                return conflict.content_id
            elif col == 2:
                return conflict.data_id
            elif col == 3:
                return conflict.instance_id
            elif col == 4:
                return conflict.title
            elif col == 5:
                return self.aliases[conflict.address] if conflict.address in self.aliases else conflict.address

        elif role == Qt.ForegroundRole:
            if col == 0 and conflict.meta_id == self.iscc[0]:
                return QVariant(QColor(Qt.red))
            if col == 1 and conflict.content_id == self.iscc[1]:
                return QVariant(QColor(Qt.red))
            if col == 2 and conflict.data_id == self.iscc[2]:
                return QVariant(QColor(Qt.red))
            if col == 3 and conflict.instance_id == self.iscc[3]:
                return QVariant(QColor(Qt.red))

        elif role == Qt.FontRole and col in [0, 1, 2, 3]:
            font = QFont("RobotoCondensed-Light", 8)
            return QVariant(font)

class ConflictTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_model = ConflictModel(self)
        self.setModel(self.table_model)
        self.setMinimumWidth(400)

        font = QFont()
        font.setFamily("Roboto Light")
        font.setPointSize(10)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
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