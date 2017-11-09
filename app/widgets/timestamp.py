# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtCore import QMimeData, QUrl, pyqtSlot, QObject, QEvent, pyqtSignal, QThread
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent
from PyQt5.QtWidgets import QWidget, QFileDialog

from app.backend.rpc import get_active_rpc_client
from app.ui.timestamp import Ui_WidgetTimestamping
from hashlib import sha256


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

        # Intercept drag & drop events from button
        self.button_dropzone.installEventFilter(self)

        # Connections
        self.button_dropzone.clicked.connect(self.file_select_dialog)
        self.button_reset.clicked.connect(self.reset)

    def process_file(self, file_path):
        log.debug('proccess file %s' % file_path)
        self.current_filepath = file_path
        self.button_dropzone.setText("Current File: %s" % os.path.basename(file_path))
        self.gbox_processing_status.setEnabled(True)
        self.progress_bar.setMaximum(os.path.getsize(file_path))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.label_processing_status.setText('Calculating fingerprint ...')
        # self.button_dropzone.setStyleSheet('background-color: #0183ea; color: white;')
        self.hash_thread = Hasher(file_path)
        self.hash_thread.hashing_progress.connect(self.progress_bar.setValue)
        self.hash_thread.finished.connect(self.hash_thread_finished)

        # Disable dropzone
        self.gbox_dropzone.setDisabled(True)
        self.button_dropzone.setDisabled(True)

        self.hash_thread.start()

    @pyqtSlot()
    def hash_thread_finished(self):
        self.current_fingerprint = self.hash_thread.result

        status_text = 'Checking timpestamp records for %s' % self.current_fingerprint
        self.label_processing_status.setText(status_text)

        # Set progress to indicate processing of undefined duration
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)

        # Check chain:
        client = get_active_rpc_client()



        log.debug('hashing finished with: %s' % self.hash_thread.result)


    @pyqtSlot()
    def file_select_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file')
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
            # self.button_dropzone.setStyleSheet('background-color: green; color: white;')
            self.button_dropzone.setText('Just drop it :)')

    def on_drag_leave(self, obj: QObject, event: QDragLeaveEvent):
        self.button_dropzone.setText('Drop your file here or click to choose.')
        # self.button_dropzone.setStyleSheet('background-color: #0183ea; color: white;')
        self.button_dropzone.style().polish(self.button_dropzone)

    def on_drop(self, obj: QObject, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.process_file(file_path)

    def reject_drag(self, event, message):
        self.button_dropzone.setText(message)
        # self.button_dropzone.setStyleSheet('background-color: red; color: white;')
        event.ignore()

    @pyqtSlot()
    def reset(self):
        self.progress_bar.hide()
        self.gbox_dropzone.setEnabled(True)
        self.gbox_verification.setDisabled(True)
        self.gbox_timestamp.setDisabled(True)
        # self.button_dropzone.setStyleSheet('background-color: #0183ea; color: white;')
        self.button_dropzone.setText('Drop your file here or click to choose.')


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
