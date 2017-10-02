#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Main UI"""
from functools import partial

from ui.ui_wallet import Ui_Wallet
from ui.pyqt_elements import get_hline, get_vline

from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton


class Ui_Main(QWidget):
    def __init__(self):
        super().__init__()
        self.views = [
            {
                'title': 'Wallet',
                'template': Ui_Wallet()
            },
            {
                'title': 'Community',
                'template': QVBoxLayout()
            }
        ]
        self.view = 0
        self.init_main_UI()

    def init_main_UI(self):
        # main window
        hbox_main = QHBoxLayout()

        # sidebar
        vbox_sidebar = self.init_sidebar_UI()
        hbox_main.addLayout(vbox_sidebar)

        hbox_main.addWidget(get_vline())

        # content window
        self.vbox_content = QVBoxLayout()
        self.vbox_content.addLayout(self.views[self.view]['template'])
        hbox_main.addLayout(self.vbox_content, 1)

        self.setLayout(hbox_main)
        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle('Content Blockchain')
        self.setWindowState(Qt.WindowMaximized)
        self.show()

    def init_sidebar_UI(self):
        vbox_sidebar = QVBoxLayout()

        label_logo = QLabel("Content-Blockchain")
        label_logo.setFont(QFont("Arial", 28))
        label_logo.setContentsMargins(0, 0, 0, 50)
        vbox_sidebar.addWidget(label_logo, alignment=Qt.AlignLeft)

        vbox_sidebar.addWidget(get_hline())
        for index, view in enumerate(self.views):
            button_menu = QPushButton(view['title'])
            button_menu.clicked.connect(partial(self.do_change_view, index))
            button_menu.setFont(QFont("Arial", 20))
            vbox_sidebar.addWidget(button_menu, alignment=Qt.AlignLeft)
            vbox_sidebar.addWidget(get_hline())

        vbox_sidebar.addStretch(1)

        return vbox_sidebar

    def do_change_view(self, new_view):
        # todo
        pass
