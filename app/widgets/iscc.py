# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
import qrcode

from PyQt5.QtCore import QAbstractTableModel, pyqtSlot, QDir, QEvent, QMimeData, QModelIndex, QObject, QUrl, Qt
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtGui import QDragLeaveEvent, QDropEvent, QFont
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QFileDialog, QHeaderView, QMenu, QTableView, QWidget

from app.ui.iscc import Ui_Widget_ISCC
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

        # Intercept drag & drop events from button
        self.button_dropzone.installEventFilter(self)

        # Connections
        self.button_dropzone.clicked.connect(self.file_select_dialog)
        self.btn_search_iscc.clicked.connect(self.search_iscc)
        self.btn_register.clicked.connect(self.register)
        self.edit_title.textChanged.connect(self.title_changed)

        self.table_iscc.setParent(None)
        table_iscc = ISCCTableView(self)
        self.tab_search.layout().insertWidget(1, table_iscc)

        self.widget_generated_iscc.setHidden(True)

    def search_iscc(self):
        pass

    def register(self):
        pass

    def title_changed(self, title):
        self.meta_id = iscc_lib.generate_meta_id(title=title)
        if self.content_id:
            self.show_conflicts()

    def process_file(self, file_path):
        self.button_dropzone.setText(file_path)
        with open(file_path, 'rb') as infile:
            self.instance_id = iscc_lib.generate_instance_id(infile)
        self.content_id = iscc_lib.generate_instance_id(b'\x00' * 16) #todo
        self.data_id = iscc_lib.generate_instance_id(b'\x11' * 16) #todo
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
        self.button_dropzone.setText('Drop your file here or click to choose.')
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

class ISCCModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.isccs = []
        self.aliases = []
        self.update_data()
        self.headers = ('ISCC', 'Title', 'Date', 'Publisher')

        # signals.votes_changed.connect(self.votes_changed)
        # signals.permissions_changed.connect(self.update_num_guardians)

    def update_data(self):
        self.isccs = [{
            'iscc': 'GRP33BK272VUD-W51K85H57OKUD-L988YUL4R1NJD-MEPU8D3L2T5ZT',
            'title': 'Title',
            'date': datetime.now(),
            'publisher': 'Publisher'
        }]

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
        if not idx.isValid():
            return None

        if role == Qt.EditRole and col == 0:
            return iscc['iscc']

        if role == Qt.DisplayRole:
            if col == 0:
                # return self.aliases[candidate.address_to]
                return iscc['iscc']
            elif col == 1:
                return iscc['title']
            elif idx.column() == 2:
                return "{}".format(iscc['date'])
            elif idx.column() == 3:
                return iscc['publisher']


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
