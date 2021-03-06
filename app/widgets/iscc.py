# -*- coding: utf-8 -*-
import logging
import os
import qrcode
import iscc
import docx2txt

from PIL.ImageQt import ImageQt
from PyQt5.QtCore import QThread

from PyQt5.QtCore import pyqtSlot, QDir, QEvent, QMimeData, QObject, QUrl
from PyQt5.QtGui import QDragLeaveEvent, QDropEvent, QPixmap, QDragEnterEvent
from PyQt5.QtWidgets import QFileDialog, QWidget
from PyQt5.QtWidgets import QMessageBox

import app
from app.backend.rpc import get_active_rpc_client
from app.models.db import data_session_scope
from app.ui.iscc import Ui_Widget_ISCC
from app.models import ISCC
from app.widgets.iscc_table import ISCCTableView
from app.widgets.iscc_conflicts_table import ConflictTableView
from app.signals import signals

log = logging.getLogger(__name__)

ACCEPTED_FILE_TYPES = ['txt', 'docx', 'png', 'jpg', 'jpeg', 'gif']


class WidgetISCC(QWidget, Ui_Widget_ISCC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self.meta_id = None
        self.content_id = None
        self.data_id = None
        self.instance_id = None
        self.instance_hash = None
        self.iscc = None
        self.conflict_in_meta = False
        self.title_formatted = None
        self.extra_formatted = None

        self.lbl_supported_types.setText("Supported file types: " + ", ".join(ACCEPTED_FILE_TYPES))

        # Intercept drag & drop events from button
        self.button_dropzone.installEventFilter(self)

        # Connections
        self.button_dropzone.clicked.connect(self.file_select_dialog)
        self.btn_search_iscc.clicked.connect(self.search_iscc)
        self.edit_search_iscc.returnPressed.connect(self.search_iscc)
        self.btn_register.clicked.connect(self.register)
        self.edit_title.textChanged.connect(self.meta_changed)
        self.edit_extra.textChanged.connect(self.meta_changed)

        self.table_iscc.setParent(None)
        self.table_iscc = ISCCTableView(self)
        self.tab_search.layout().insertWidget(1, self.table_iscc)

        self.widget_generated_iscc.setHidden(True)
        self.label_title_conflicts.setHidden(True)
        self.table_conflicts.setParent(None)
        self.table_conflicts = ConflictTableView(self)
        self.table_conflicts.setHidden(True)
        self.tab_register.layout().insertWidget(5, self.table_conflicts)
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
        data = {
            'json': {
                'title': self.title_formatted,
                'tophash': self.instance_hash
            }
        }
        if self.extra_formatted:
            data['json']['extra'] = self.extra_formatted
        try:
            client.publish(app.STREAM_ISCC, [self.meta_id, self.content_id, self.data_id, self.instance_id], data)
            self.edit_title.clear()
            self.label_qr.clear()
            self.label_iscc.clear()
            self.meta_id = None
            self.content_id = None
            self.data_id = None
            self.instance_id = None
            self.iscc = None
            self.title_formatted = None
            self.extra_formatted = None
            self.instance_hash = None
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

    def meta_changed(self):
        title = self.edit_title.text()
        extra = self.edit_extra.text()
        mid, tf, ef = iscc.meta_id(title=title, extra=extra)
        self.meta_id = mid
        self.title_formatted = tf
        self.extra_formatted = ef
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
        filter = "Text files and Images (*." + " *.".join(ACCEPTED_FILE_TYPES) + ")"
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', QDir().homePath(), filter)
        if file_path:
            self.button_dropzone.setStyleSheet('QPushButton:enabled {background-color: #0183ea; color: white;}')
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
            if url.fileName().split('.')[-1] not in ACCEPTED_FILE_TYPES:
                return self.reject_drag(event, 'Filetype not supported. Try again!')

            event.accept()
            self.button_dropzone.setStyleSheet('QPushButton:enabled {background-color: #0183ea; color: white;}')
            self.button_dropzone.setText('Just drop it :)')

    def on_drag_leave(self, obj: QObject, event: QDragLeaveEvent):
        self.button_dropzone.setText('Drop your image or text file here or click to choose.')
        self.button_dropzone.style().polish(self.button_dropzone)

    def on_drop(self, obj: QObject, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.process_file(file_path)

    def reject_drag(self, event, message):
        self.button_dropzone.setText(message)
        self.button_dropzone.setStyleSheet('QPushButton:enabled {background-color: red; color: white;}')
        event.ignore()

    def show_conflicts(self):
        self.widget_generated_iscc.setHidden(False)
        self.iscc = self.meta_id + '-' + self.content_id + '-' + self.data_id + '-' + self.instance_id
        self.label_iscc.setText(self.iscc)
        img = qrcode.make(self.meta_id + self.content_id + self.data_id + self.instance_id)
        pixmap = QPixmap.fromImage(ImageQt(img))
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
        file_ending = self.file_path.split('.')[-1]
        if file_ending in ['jpg', 'png', 'jpeg', 'gif']:
            self.parent.content_id = iscc.content_id_image(self.file_path)
        elif file_ending == 'txt':
            with open(self.file_path, encoding='utf-8') as infile:
                self.parent.content_id = iscc.content_id_text(infile.read())
        elif file_ending == 'docx':
            self.parent.content_id = iscc.content_id_text(docx2txt.process(self.file_path))

        self.parent.instance_id, self.parent.instance_hash = iscc.instance_id(self.file_path)
        self.parent.data_id = iscc.data_id(self.file_path)

        if self.parent.meta_id:
            self.parent.show_conflicts()
