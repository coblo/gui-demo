import codecs
import json
import os
import time

from PIL import Image

from app.ui.create_privilege_request import Ui_widget_create_privilege_request
from app.backend.api import Api

from PyQt5.QtCore import QSizeF, Qt
from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QDialog, QWidget, QFileDialog, QMessageBox


class CreatePrivilegeRequest(QWidget, Ui_widget_create_privilege_request):
    def __init__(self, parent, change_stack_index):
        super().__init__(parent)
        self.api = Api()
        self.setupUi(self)
        self.parent = parent
        self.image_code = None

        # hide unneccessary things for upload
        self.btn_change_image.setHidden(True)
        self.label_img_path.setHidden(True)
        self.btn_send_request.setDisabled(True)

        # connect input fields
        self.input_name.textChanged.connect(self.input_changed)
        self.check_guardian.stateChanged.connect(self.input_changed)
        self.check_validator.stateChanged.connect(self.input_changed)

        # connect buttons
        self.btn_print_proof.clicked.connect(self.print_proof)
        self.btn_upload_photo.clicked.connect(self.upload_image)
        self.btn_change_image.clicked.connect(self.upload_image)
        self.btn_send_request.clicked.connect(self.send_request)

        self.updater = parent.updater
        self.updater.permissions_changed.connect(self.on_skills_changed)

    def on_skills_changed(self, skills):
        if 'admin' in skills:
            self.check_guardian.setHidden(True)
        if 'mine' in skills:
            self.check_validator.setHidden(True)

    def print_proof(self):
        printer = QPrinter(96)
        printer.setOrientation(QPrinter.Landscape)
        printer.setOutputFileName('tmp.pdf')
        printer.setPageMargins(16, 12, 20, 12, QPrinter.Millimeter)

        text = "Date:\n{}\n\n".format(time.strftime("%d/%m/%Y"))
        text += "Address:\n{}\n\n".format(self.api.get_main_address())
        text += "Current Blockhash:\n{}".format(self.api.get_actual_hash())

        document = QTextDocument()
        document.setPageSize(QSizeF(printer.pageRect().size()))
        document.setDefaultFont(QFont("Arial", 30))
        document.setPlainText(text)

        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            dialog.printer().setOrientation(QPrinter.Landscape)
            document.print_(dialog.printer())

    def upload_image(self):
        file = QFileDialog.getOpenFileName(filter="Images (*.png *.jpg)")

        if file:
            image = Image.open(file[0])
            width, height = image.size
            if width > 800 or height > 800:
                message_box = QMessageBox()
                message_box.setWindowTitle("Wrong Image Size")
                message_box.setText("Please select an image smaller than 800 x 800")
                message_box.exec()
            else:
                jpg_image = image.convert('L')
                jpg_image.save('tmp.jpg', 'JPEG', quality=40)
                with open('tmp.jpg', 'rb') as f:
                    self.image_code = f.read()
                os.remove('tmp.jpg')

                self.widget_photo_upload.setHidden(True)
                self.label_img_path.setText(file[0])
                self.label_img_path.setHidden(False)
                self.btn_change_image.setHidden(False)

                self.input_changed()

    def send_request(self):
        data = {
            'image': self.image_code.hex()
        }
        if len(self.input_mail.text()) > 0:
            data['mail'] = self.input_mail.text()
        if len(self.input_description.toPlainText()) > 0:
            data['description'] = self.input_description.toPlainText()
        skills = []
        if self.check_validator.checkState() == Qt.Checked:
            skills.append('validator')
        if self.check_guardian.checkState() == Qt.Checked:
            skills.append('guardian')
        data['skills'] = skills
        key = self.input_name.text()
        data_hex = codecs.encode(json.dumps(data).encode('utf-8'), 'hex')

        if self.api.publish(stream='privilege-requests', key=key, data=data_hex.decode('ascii')):
            self.parent.change_stack_index(1)

    def input_changed(self):
        valid = True
        if self.image_code is None:
            valid = False
        if len(self.input_name.text()) == 0:
            valid = False
        if not self.check_validator.checkState() == Qt.Checked and not self.check_guardian.checkState() == Qt.Checked:
            valid = False
        self.btn_send_request.setDisabled(not valid)
