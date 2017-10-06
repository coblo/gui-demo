#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Community UI"""
import codecs
import io
import json
from datetime import date

from PIL import Image, ImageQt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget, QPushButton

from multichain_api import Multichain_Api


class Ui_Review_Requests(QWidget):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.font_l = QFont("Arial", 16)
        self.font_s = QFont("Arial", 12)
        self.multichain = Multichain_Api()
        self.init_main_ui()

    def init_main_ui(self):
        vbox_main = QVBoxLayout()

        hbox_title = QHBoxLayout()
        label_heading = QLabel("Review Privilege Requests")
        label_heading.setFont(QFont("Arial", 28))
        hbox_title.addWidget(label_heading, alignment=Qt.AlignLeft)
        label_balance = QLabel("Total Balance: {} Koin".format(self.multichain.get_balance()))
        label_balance.setFont(self.font_s)
        hbox_title.addWidget(label_balance, alignment=Qt.AlignRight)
        vbox_main.addLayout(hbox_title)

        vbox_main.addSpacing(50)

        vbox_requests = QVBoxLayout()
        requests = self.multichain.get_stream_items('privilege-requests')
        for index, request in enumerate(requests):
            vbox_requests.addLayout(self.hbox_request_item(index, request))
        vbox_main.addLayout(vbox_requests)
        vbox_main.addStretch(1)

        self.setLayout(vbox_main)

    def hbox_request_item(self, index,  request):
        data = request['data']
        data = codecs.decode(data.encode('ascii'), 'hex')
        data_json = json.loads(data.decode('utf-8'))
        image_data = bytes.fromhex(data_json['image'])
        image = Image.open(io.BytesIO(image_data))
        image_qt = ImageQt.ImageQt(image)

        hbox_main = QHBoxLayout()

        label_image = QLabel(self)
        # todo show only thumbnail and whole image on click or hover
        label_image.setPixmap(QPixmap.fromImage(image_qt))
        hbox_main.addWidget(label_image)

        address = request['publishers'][0]
        vbox_data = QVBoxLayout()
        label_name = QLabel(request['key'])
        label_name.setFont(self.font_l)
        vbox_data.addWidget(label_name, alignment=Qt.AlignTop)
        label_address = QLabel(address)
        label_address.setFont(self.font_s)
        vbox_data.addWidget(label_address, alignment=Qt.AlignTop)
        label_date = QLabel("{}".format(date.fromtimestamp(request['blocktime'])))
        label_date.setFont(self.font_s)
        vbox_data.addWidget(label_date, alignment=Qt.AlignTop)
        if 'mail' in data_json:
            label_mail = QLabel(data_json['mail'])
            label_mail.setFont(self.font_s)
            vbox_data.addWidget(label_mail, alignment=Qt.AlignTop)
        # todo existing permissions
        vbox_data.addStretch(1)
        hbox_main.addLayout(vbox_data)

        vbox_buttons = QVBoxLayout()
        label_description = QLabel(data_json['description'])
        label_description.setFont(self.font_s)
        vbox_buttons.addWidget(label_description, alignment=Qt.AlignTop)
        hbox_buttons = QHBoxLayout()
        for key in data_json['privileges']:
            button = QPushButton("Grant {}".format(key.title()))
            button.setFont(self.font_s)
            hbox_buttons.addWidget(button, alignment=Qt.AlignRight)
        vbox_buttons.addLayout(hbox_buttons)
        hbox_main.addLayout(vbox_buttons)

        return hbox_main