#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Community UI"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget

from multichain_api import Multichain_Api


class Ui_Community(QWidget):
    def __init__(self):
        super().__init__()
        self.font_heading = QFont("Arial", 20)
        self.multichain = Multichain_Api()
        self.init_main_ui()

    def init_main_ui(self):
        vbox_main = QVBoxLayout()

        hbox_title = QHBoxLayout()
        label_heading = QLabel("Community")
        label_heading.setFont(QFont("Arial", 28))
        hbox_title.addWidget(label_heading, alignment=Qt.AlignLeft)
        label_balance = QLabel("Total Balance: {} Koin".format(self.multichain.get_balance()))
        label_balance.setFont(QFont("Arial", 12))
        hbox_title.addWidget(label_balance, alignment=Qt.AlignRight)
        vbox_main.addLayout(hbox_title)

        vbox_main.addStretch(1)

        self.setLayout(vbox_main)