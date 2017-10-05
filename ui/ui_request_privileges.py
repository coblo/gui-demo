#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Request Privileges UI"""
import time

from PyQt5.QtCore import QSizeF
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget, QPushButton, QGridLayout, QLineEdit, QTextEdit, \
    QCheckBox

from multichain_api import Multichain_Api


class Ui_Request_Privileges(QWidget):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.font_s = QFont("Arial", 12)
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

        vbox_main.addStretch(1)

        self.setLayout(vbox_main)

    def layout_form(self):
        layout_form = QGridLayout()

        label_photo = QLabel("Photo*:")
        label_photo.setFont(self.font_s)
        layout_form.addWidget(label_photo, 1, 1)
        hbox_photo = QHBoxLayout()
        button_print = QPushButton("Print Proof Now")
        button_print.setFont(self.font_s)
        button_print.clicked.connect(self.do_print_proof)
        hbox_photo.addWidget(button_print, alignment=Qt.AlignLeft)
        button_upload = QPushButton("Upload Photo")
        button_upload.setFont(self.font_s)
        button_print.clicked.connect(self.do_upload_image)
        # todo text
        hbox_photo.addWidget(button_upload, alignment=Qt.AlignRight)
        layout_form.addLayout(hbox_photo, 1, 2)

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
            input_validator = QCheckBox(
                "Validator (You have to run a permanent node and you can earn koins by validating blocks)")
            input_validator.setFont(self.font_s)
            vbox_privileges.addWidget(input_validator, alignment=Qt.AlignLeft)
        if not self.multichain.is_admin():
            input_guardian = QCheckBox("Guardian (You can grant and revoke permissions for other users)")
            input_guardian.setFont(self.font_s)
            vbox_privileges.addWidget(input_guardian, alignment=Qt.AlignLeft)
        layout_form.addLayout(vbox_privileges, 5, 2)

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
        pass
