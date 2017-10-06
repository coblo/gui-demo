#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Request Privileges UI"""
import base64
import codecs
import io
import json
import os
import time
from PIL import Image

from PyQt5.QtCore import QSizeF, Qt
from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget, QPushButton, QGridLayout, QLineEdit, QTextEdit, \
    QCheckBox, QFileDialog, QDialog
from PyQt5.QtWidgets import QMessageBox

from multichain_api import Multichain_Api


class Ui_Request_Privileges(QWidget):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.font_s = QFont("Arial", 12)
        self.font_l = QFont("Arial", 16)
        self.image_code = None
        self.multichain = Multichain_Api()
        self.init_main_ui()

    def init_main_ui(self):
        vbox_main = QVBoxLayout()

        hbox_title = QHBoxLayout()
        label_heading = QLabel("Request Community Privileges")
        label_heading.setFont(QFont("Arial", 28))
        hbox_title.addWidget(label_heading, alignment=Qt.AlignLeft)
        label_balance = QLabel("Total Balance: {} Koin".format(self.multichain.get_balance()))
        label_balance.setFont(QFont("Arial", 12))
        hbox_title.addWidget(label_balance, alignment=Qt.AlignRight)
        vbox_main.addLayout(hbox_title)

        vbox_main.addStretch(1)

        vbox_main.addLayout(self.layout_form())

        button_send = QPushButton("Send Request")
        button_send.setFont(self.font_l)
        button_send.clicked.connect(self.do_send_request)
        vbox_main.addWidget(button_send, alignment=Qt.AlignRight)

        vbox_main.addStretch(1)

        self.setLayout(vbox_main)

    def layout_form(self):
        layout_form = QGridLayout()

        label_photo = QLabel("Photo*:")
        label_photo.setFont(self.font_s)
        layout_form.addWidget(label_photo, 1, 1)
        self.hbox_photo = QHBoxLayout()
        button_print = QPushButton("Print Proof Now")
        button_print.setFont(self.font_s)
        button_print.clicked.connect(self.do_print_proof)
        self.hbox_photo.addWidget(button_print, alignment=Qt.AlignLeft)
        self.button_upload = QPushButton("Upload Photo")
        self.button_upload.setFont(self.font_s)
        self.button_upload.clicked.connect(self.do_upload_image)
        # todo text
        self.hbox_photo.addWidget(self.button_upload, alignment=Qt.AlignRight)
        layout_form.addLayout(self.hbox_photo, 1, 2)

        label_name = QLabel("Your Name*:")
        label_name.setFont(self.font_s)
        layout_form.addWidget(label_name, 2, 1)
        self.input_name = QLineEdit()
        layout_form.addWidget(self.input_name, 2, 2)

        label_mail = QLabel("E-Mail:")
        label_mail.setFont(self.font_s)
        layout_form.addWidget(label_mail, 3, 1)
        self.input_mail = QLineEdit()
        # todo text
        layout_form.addWidget(self.input_mail, 3, 2)

        label_description = QLabel("Description:")
        label_description.setFont(self.font_s)
        layout_form.addWidget(label_description, 4, 1)
        self.input_description = QTextEdit()
        layout_form.addWidget(self.input_description, 4, 2)

        label_privileges = QLabel("Privileges Requested:")
        label_privileges.setFont(self.font_s)
        layout_form.addWidget(label_photo, 5, 1)
        vbox_privileges = QVBoxLayout()
        if not self.multichain.is_miner():
            self.input_validator = QCheckBox(
                "Validator (You have to run a permanent node and you can earn koins by validating blocks)")
            self.input_validator.setFont(self.font_s)
            vbox_privileges.addWidget(self.input_validator, alignment=Qt.AlignLeft)
        if not self.multichain.is_admin():
            self.input_guardian = QCheckBox("Guardian (You can grant and revoke permissions for other users)")
            self.input_guardian.setFont(self.font_s)
            vbox_privileges.addWidget(self.input_guardian, alignment=Qt.AlignLeft)
        layout_form.addLayout(vbox_privileges, 5, 2)

        layout_form.setColumnStretch(1, 1)
        layout_form.setColumnStretch(2, 6)

        return layout_form

    def do_print_proof(self):
        printer = QPrinter(96)
        printer.setOrientation(QPrinter.Landscape)
        printer.setOutputFileName('tmp.pdf')
        printer.setPageMargins(16, 12, 20, 12, QPrinter.Millimeter)

        text = "Date:\n{}\n\n".format(time.strftime("%d/%m/%Y"))
        text += "Address:\n{}\n\n".format(self.multichain.get_address())
        text += "Current Blockhash:\n{}".format(self.multichain.get_actual_hash())

        document = QTextDocument()
        document.setPageSize(QSizeF(printer.pageRect().size()))
        document.setDefaultFont(QFont("Arial", 30))
        document.setPlainText(text)

        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            dialog.printer().setOrientation(QPrinter.Landscape)
            document.print_(dialog.printer())

    def do_upload_image(self):
        first_try = self.image_code is None
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

                if first_try:
                    self.hbox_photo.removeWidget(self.button_upload)
                    self.button_upload.deleteLater()
                    self.label_image_path = QLabel(file[0])
                    self.label_image_path.setFont(self.font_s)
                    self.hbox_photo.addWidget(self.label_image_path, alignment=Qt.AlignCenter)
                    button_change = QPushButton("Change Image")
                    button_change.setFont(self.font_s)
                    button_change.clicked.connect(self.do_upload_image)
                    self.hbox_photo.addWidget(button_change, alignment=Qt.AlignRight)
                else:
                    self.label_image_path.setText(file[0])

    def do_send_request(self):
        # todo: disable button when there is no name or no photo
        data = {
            'image': self.image_code.hex(),
        }
        if len(self.input_mail.text()) > 0:
            data['mail'] = self.input_mail.text()
        if len(self.input_description.toPlainText()) > 0:
            data['description'] = self.input_description.toPlainText()
        privileges = []
        if not self.multichain.is_miner() and self.input_validator.checkState() == Qt.Checked:
            privileges.append('validator')
        if not self.multichain.is_admin() and self.input_guardian.checkState() == Qt.Checked:
            privileges.append('guardian')
        data['privileges'] = privileges
        key = self.input_name.text()
        data_hex = codecs.encode(json.dumps(data).encode('utf-8'), 'hex')

        self.multichain.publish(stream='privilege-requests', key=key, data=data_hex.decode('ascii'))
