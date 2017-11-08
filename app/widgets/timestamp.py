# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtCore import QMimeData, QUrl, pyqtSlot, QObject, QEvent
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent
from PyQt5.QtWidgets import QWidget
from app.ui.timestamp import Ui_WidgetTimestamping
from hashlib import sha256


log = logging.getLogger(__name__)


class WidgetTimestamping(QWidget, Ui_WidgetTimestamping):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.reset()

        self.button_dropzone.installEventFilter(self)

        # Connections
        self.button_reset.clicked.connect(self.reset)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.DragEnter:
            log.debug('DragEnter')
            self.on_drag_enter(obj, event)
        elif event.type() == QEvent.DragLeave:
            log.debug('DragLeave')
            self.on_drag_leave(obj, event)
        elif event.type() == QEvent.Drop:
            log.debug('Drop')
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
            elif not url.isLocalFile():
                return self.reject_drag(event, 'Only local files are supported. Try again!')
            elif os.path.isdir(url.toLocalFile()):
                return self.reject_drag(event, 'Directories not supported. Try again!')
            else:
                event.accept()

    def on_drag_leave(self, obj: QObject, event: QDragLeaveEvent):
        self.button_dropzone.setText('Drop your file here or click to choose.')
        self.button_dropzone.setStyleSheet('background-color: #0183ea; color: white;')
        self.button_dropzone.style().polish(self.button_dropzone)
        event.accept()

    def reject_drag(self, event, message):
        self.button_dropzone.setText(message)
        self.button_dropzone.setStyleSheet('background-color: red; color: white;')
        event.ignore()

    @pyqtSlot()
    def reset(self):
        self.progress_bar.hide()
        self.gbox_dropzone.setEnabled(True)
        self.gbox_verification.setDisabled(True)
        self.gbox_timestamp.setDisabled(True)
        self.button_dropzone.setStyleSheet('background-color: #0183ea; color: white;')
        self.button_dropzone.setText('Drop your file here or click to choose.')

    def set_file(self, file_path):
        self.file = file_path
        text = "Current File: %s" % os.path.basename(self.file)
        self.lbl_dropzone.setText(text)
        self.progress_bar.show()
        self.calc_sha256()

    def calc_sha256(self):
        hasher = sha256()
        progress = 0
        with open(self.file, 'rb') as f:
            while True:
                chunk = f.read(64)
                if not chunk:
                    break
                else:
                    hasher.update(chunk)
                    progress += len(chunk)
                    self.progress_bar.setValue(progress)
        self.lbl_dropzone.setText(hasher.hexdigest())


    def dropEvent(self, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.set_file(file_path)
        event.accept()
        log.debug('TODO: hash and register: %s' % file_path)


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets, QtCore
    from app import helpers
    helpers.init_logging()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('fusion')
    dialog = WidgetTimestamping()
    dialog.show()
    sys.exit(app.exec())
