# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtCore import QMimeData, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent
from PyQt5.QtWidgets import QWidget
from app.ui.timestamp import Ui_wgt_page_timestamping


log = logging.getLogger(__name__)


class TimeStampWidget(QWidget, Ui_wgt_page_timestamping):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        mimedata = event.mimeData()
        assert isinstance(mimedata, QMimeData)
        if mimedata.hasUrls():
            if len(mimedata.urls()) > 1:
                self.lbl_dropzone.setText('One file at a time please. Try again!')
                event.ignore()
                return
            url = mimedata.urls()[0]
            assert isinstance(url, QUrl)
            if not url.isValid():
                self.lbl_dropzone.setText('Invalid URL. Try again!')
                event.ignore()
                return
            if not url.isLocalFile():
                self.lbl_dropzone.setText('Only local files are supported. Try again!')
                event.ignore()
                return
            if os.path.isdir(url.toLocalFile()):
                self.lbl_dropzone.setText('Directories not supported. Try again!')
                event.ignore()
                return
            event.accept()

    def dropEvent(self, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        log.debug('TODO: hash and register: %s' % file_path)


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets
    from app import helpers
    helpers.init_logging()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('fusion')
    dialog = TimeStampWidget()
    dialog.show()
    sys.exit(app.exec())
