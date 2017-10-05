#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Community UI"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QWidget
from PyQt5.QtWidgets import QPushButton

from multichain_api import Multichain_Api


class Ui_Community(QWidget):
    def __init__(self):
        super().__init__()
        self.font_heading = QFont("Arial", 20)
        self.font_l = QFont("Arial", 16)
        self.font_s = QFont("Arial", 12)
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

        vbox_main.addWidget(self.widget_administrate_community(), alignment=Qt.AlignCenter)

        vbox_main.addStretch(1)

        # todo: webview

        vbox_main.addWidget(self.widget_privileges(), alignment=Qt.AlignCenter)

        vbox_main.addStretch(1)

        self.setLayout(vbox_main)

    def widget_administrate_community(self):
        widget_administrate = QWidget()
        layout_administrate = QVBoxLayout()

        hbox_active_validators = QHBoxLayout()
        label_active_validators = QLabel(
            "{}% of validators are active".format(int(self.multichain.get_miner_info()['active'] * 100)))
        label_active_validators.setFont(self.font_l)
        hbox_active_validators.addWidget(label_active_validators, alignment=Qt.AlignLeft)
        button_active_validators = QPushButton("{} Validators".format("Review" if self.multichain.is_admin() else "Watch"))
        button_active_validators.setFixedWidth(200)
        button_active_validators.setFont(self.font_l)
        hbox_active_validators.addWidget(button_active_validators, alignment=Qt.AlignRight)
        layout_administrate.addLayout(hbox_active_validators)

        hbox_active_guardians = QHBoxLayout()
        label_active_guardians = QLabel(
            "{}% of guardians are active".format(int(self.multichain.get_admin_info()['active'] * 100)))
        label_active_guardians.setFont(self.font_l)
        hbox_active_guardians.addWidget(label_active_guardians, alignment=Qt.AlignLeft)
        button_active_guardians = QPushButton("{} Guardians".format("Review" if self.multichain.is_admin() else "Watch"))
        button_active_guardians.setFixedWidth(200)
        button_active_guardians.setFont(self.font_l)
        hbox_active_guardians.addWidget(button_active_guardians, alignment=Qt.AlignRight)
        layout_administrate.addLayout(hbox_active_guardians)

        if self.multichain.is_admin():
            hbox_nodes_waiting = QHBoxLayout()
            label_nodes_waiting = QLabel("{} nodes waiting for permissions".format(0))  # todo
            label_nodes_waiting.setFont(self.font_l)
            hbox_nodes_waiting.addWidget(label_nodes_waiting, alignment=Qt.AlignLeft)
            button_nodes_waiting = QPushButton("Approve Requests")
            button_nodes_waiting.setFixedWidth(200)
            button_nodes_waiting.setFont(self.font_l)
            hbox_nodes_waiting.addWidget(button_nodes_waiting, alignment=Qt.AlignRight)
            layout_administrate.addLayout(hbox_nodes_waiting)

        widget_administrate.setLayout(layout_administrate)
        widget_administrate.setFixedWidth(600)
        return widget_administrate

    def widget_privileges(self):
        widget_privileges = QWidget()
        layout_privileges = QHBoxLayout()

        layout_status = QVBoxLayout()
        label_validator = QLabel("You are a validator: {}".format("✔" if self.multichain.is_miner() else "✖"))
        label_validator.setFont(self.font_s)
        layout_status.addWidget(label_validator, alignment=Qt.AlignLeft)
        label_guardian = QLabel("You are a guardian: {}".format("✔" if self.multichain.is_admin() else "✖"))
        label_guardian.setFont(self.font_s)
        layout_status.addWidget(label_guardian, alignment=Qt.AlignLeft)

        layout_privileges.addLayout(layout_status)

        button_request = QPushButton("Request Privileges from Community")
        button_request.setFont(self.font_l)
        layout_privileges.addWidget(button_request)

        widget_privileges.setLayout(layout_privileges)
        widget_privileges.setFixedWidth(600)
        return widget_privileges
