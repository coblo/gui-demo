# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
from hashlib import sha256

from PyQt5.QtCore import QMimeData, QUrl, pyqtSlot, QObject, QEvent, pyqtSignal, QThread, QDir
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent
from PyQt5.QtWidgets import QWidget, QFileDialog, QTableWidgetItem, QHeaderView, QMessageBox

from app.api import get_timestamps, put_timestamp
from app.exceptions import RpcResponseError
from app.ui.timestamp import Ui_WidgetTimestamping

log = logging.getLogger(__name__)


class Hasher(QThread):

    #: emits num bytes processed
    hashing_progress = pyqtSignal(int)

    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self.result = None

    def run(self):
        hasher = sha256()
        progress = 0
        with open(self.file_path, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                else:
                    hasher.update(chunk)
                    progress += len(chunk)
                    self.hashing_progress.emit(progress)
        self.result = hasher.hexdigest()


class WidgetTimestamping(QWidget, Ui_WidgetTimestamping):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.reset()
        self.hash_thread = None
        self.current_fingerprint = None
        self.current_filepath = None
        self.current_comment = None

        # Ui Tweaks
        self.table_verification.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # Intercept drag & drop events from button
        self.button_dropzone.installEventFilter(self)

        # Connections
        self.button_dropzone.clicked.connect(self.file_select_dialog)
        self.button_reset.clicked.connect(self.reset)
        self.button_register.clicked.connect(self.register_timestamp)

    def process_file(self, file_path):
        log.debug('proccess file %s' % file_path)
        self.current_filepath = file_path
        self.button_dropzone.setText("Current File: %s" % os.path.basename(file_path))
        self.gbox_processing_status.setEnabled(True)
        self.progress_bar.setMaximum(os.path.getsize(file_path))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.label_processing_status.setText('Calculating fingerprint ...')
        self.hash_thread = Hasher(file_path)
        self.hash_thread.hashing_progress.connect(self.progress_bar.setValue)
        self.hash_thread.finished.connect(self.hash_thread_finished)

        # Disable dropzone
        self.gbox_dropzone.setDisabled(True)
        self.button_dropzone.setDisabled(True)

        self.hash_thread.start()

    @pyqtSlot()
    def hash_thread_finished(self):
        log.debug('hash thread finished with: %s' % self.hash_thread.result)

        self.current_fingerprint = self.hash_thread.result
        status_text = 'Checking timpestamp records for %s' % self.current_fingerprint
        self.label_processing_status.setText(status_text)

        # Set progress to indicate processing of undefined duration
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)

        # Check for existing timestamps:
        try:
            timestamps = get_timestamps(self.current_fingerprint)
        except RpcResponseError as e:
            QMessageBox.warning(self, 'Error reading timestamp stream', str(e))
            timestamps = None

        if timestamps:
            self.label_verification.setText('Found existing timestamps for document:')
            self.gbox_verification.setEnabled(True)
            self.table_verification.setRowCount(len(timestamps))
            for row_id, row in enumerate(timestamps):
                for col_id, col in enumerate(row):
                    if col_id == 0:
                        content = QTableWidgetItem('%s' % datetime.fromtimestamp(col))
                    else:
                        content = QTableWidgetItem(col)
                    self.table_verification.setItem(row_id, col_id, content)
        else:
            self.table_verification.hide()
            self.label_verification.setText('No previous timestamps found for this document.')

        self.progress_bar.hide()
        self.label_processing_status.setText('Fingerprint: %s' % self.current_fingerprint)
        self.gbox_timestamp.setEnabled(True)

    @pyqtSlot()
    def register_timestamp(self):
        self.button_register.setDisabled(True)
        self.edit_comment.setDisabled(True)
        try:
            txid = put_timestamp(self.current_fingerprint, self.edit_comment.text())
            self.edit_comment.hide()
            self.label_register_comment.setText(
                'Timestamp registered. Transaction ID is: %s' % txid
            )
        except Exception as e:
            self.edit_comment.hide()
            self.label_register_comment.setText(
                'Registration failed: %s' % e
            )

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

    def reject_drag(self, event, message):
        self.button_dropzone.setText(message)
        self.button_dropzone.setStyleSheet(
            'QPushButton:enabled {background-color: red; color: white;}'
        )
        event.ignore()

    @pyqtSlot()
    def reset(self):
        self.current_fingerprint = None
        self.current_filepath = None

        # Dropzone
        self.gbox_dropzone.setEnabled(True)
        self.button_dropzone.setEnabled(True)
        self.button_dropzone.setText('Drop your file here or click to choose.')

        # Processing Status
        self.gbox_processing_status.show()
        self.gbox_processing_status.setDisabled(True)
        self.label_processing_status.setText('Waiting for document to process')
        self.progress_bar.hide()

        # Verification results
        self.gbox_verification.setDisabled(True)
        self.label_verification.setText('Waiting for document to verify')
        self.table_verification.clearContents()
        self.table_verification.setRowCount(0)
        self.table_verification.show()

        # Timestamp Form
        self.gbox_timestamp.setDisabled(True)
        self.label_register_comment.setText(
            'You may add a public comment to your timestamp if you wish'
        )
        self.edit_comment.clear()
        self.edit_comment.show()
        self.edit_comment.setEnabled(True)
        self.button_reset.setEnabled(True)
        self.button_register.setEnabled(True)


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    import app
    app.init()
    wrapper = QtWidgets.QApplication(sys.argv)
    wrapper.setStyle('fusion')
    dialog = WidgetTimestamping()
    dialog.show()
    sys.exit(wrapper.exec())
