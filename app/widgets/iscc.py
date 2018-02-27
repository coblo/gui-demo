# -*- coding: utf-8 -*-
import base64
import logging
import os
from binascii import hexlify
import qrcode
import ubjson
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtCore import pyqtSlot, QDir, QEvent, QMimeData, QObject, QUrl
from PyQt5.QtGui import QDragLeaveEvent, QDropEvent, QPixmap, QDragEnterEvent
from PyQt5.QtWidgets import QFileDialog, QWidget
from PyQt5.QtWidgets import QMessageBox

from app.backend.rpc import get_active_rpc_client
from app.models.db import data_session_scope
from app.ui.iscc import Ui_Widget_ISCC
from app.models import ISCC
from app.tools import iscc as iscc_lib
from app.widgets.iscc_table import ISCCTableView
from app.widgets.iscc_conflicts_table import ConflictTableView
from app.signals import signals

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
        self.balance_is_zero = True

        signals.iscc_inserted.connect(self.update_conflicts)
        signals.on_balance_status_changed.connect(self.on_balance_status_changed)

    def on_balance_status_changed(self, balance_is_zero):
        self.balance_is_zero = balance_is_zero
        if balance_is_zero:
            self.btn_register.setDisabled(True)
            self.btn_register.setToolTip("You need coins to register an ISCC.")
        else:
            self.btn_register.setToolTip("")

    def search_iscc(self):  # todo: wenn man einen ganzen iscc sucht findet man nichts...
        search_term = self.edit_search_iscc.text()
        self.table_iscc.model().update_data(search_term)

    def register(self):
        client = get_active_rpc_client()
        data = dict(title=self.edit_title.text())
        serialized = ubjson.dumpb(data)
        data_hex = hexlify(serialized).decode('utf-8')
        try:
            client.publish('testiscc', self.iscc, data_hex)
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
            self.label_title_conflicts.setHidden(True)
            self.table_conflicts.setHidden(True)
            signals.new_unconfirmed.emit('ISCC registration')
        except Exception as e:
            QMessageBox.warning(QMessageBox(), 'Error while publishing', str(e), QMessageBox.Close,
                                QMessageBox.Close)

    def update_conflicts(self):
        if self.iscc:
            self.show_conflicts()

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
        self.current_filepath = file_path
        self.button_dropzone.setText("Processing File...")
        self.button_dropzone.setDisabled(True)
        self.hash_thread = ISCCGEnerator(file_path, self)
        self.hash_thread.finished.connect(self.hash_thread_finished)

        self.hash_thread.start()

    @pyqtSlot()
    def hash_thread_finished(self):
        self.button_dropzone.setDisabled(False)
        self.button_dropzone.setText(self.current_filepath.split("/")[-1])

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
            if not self.balance_is_zero:
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

class ISCCGEnerator(QThread):

    #: emits num bytes processed

    def __init__(self, file_path, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self.result = None
        self.parent = parent

    def run(self):
        with open(self.file_path, 'rb') as infile:
            self.parent.instance_id = iscc_lib.generate_instance_id(infile)
        if self.file_path.split('.')[-1] in ['jpg', 'png', 'jpeg']:
            self.parent.content_id = iscc_lib.generate_image_hash(self.file_path)
        else:
            self.parent.content_id = base64.b32encode(b'\x10' +  os.urandom(7)).rstrip(b'=').decode('ascii') # todo
        with open(self.file_path, 'rb') as infile:
            self.parent.data_id = iscc_lib.generate_data_id(infile)
        if self.parent.meta_id:
            self.parent.show_conflicts()