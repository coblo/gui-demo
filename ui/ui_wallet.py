#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Wallet UI"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSizePolicy, QTableWidget, \
    QTableWidgetItem, QWidget

from multichain_api import Multichain_Api
from ui.pyqt_elements import get_hline, get_vline


class Ui_Wallet(QWidget):
    def __init__(self):
        super().__init__()
        self.font_heading = QFont("Arial", 20)
        self.font_form = QFont("Arial", 12)
        self.multichain = Multichain_Api()
        self.init_main_ui()

    def init_main_ui(self):
        vbox_main = QVBoxLayout()
        hbox_title = QHBoxLayout()
        label_heading = QLabel("Wallet")
        label_heading.setFont(QFont("Arial", 28))
        hbox_title.addWidget(label_heading, alignment=Qt.AlignLeft)
        label_balance = QLabel("Total Balance: {} Koin".format(self.multichain.get_balance()))
        label_balance.setFont(QFont("Arial", 12))
        hbox_title.addWidget(label_balance, alignment=Qt.AlignRight)
        vbox_main.addLayout(hbox_title)

        hbox_top = QHBoxLayout()
        hbox_top.addLayout(self.init_addresses_ui(), 1)
        hbox_top.addWidget(get_vline())
        hbox_top.addLayout(self.init_send_ui(), 1)
        vbox_main.addLayout(hbox_top, 1)

        vbox_main.addWidget(get_hline())

        vbox_main.addLayout(self.init_history_ui(), 1)

        vbox_main.addStretch(1)

        self.setLayout(vbox_main)

    def init_addresses_ui(self):
        vbox_addresses = QVBoxLayout()
        label_heading = QLabel("My Addresses")
        label_heading.setFont(self.font_heading)
        vbox_addresses.addWidget(label_heading, alignment=Qt.AlignLeft)

        balances = self.multichain.get_balances()
        table_addresses = QTableWidget(len(balances), 2)
        table_addresses.setHorizontalHeaderLabels(['Address', 'Balance'])
        col = 0
        for address in balances:
            item_address = QTableWidgetItem(address['address'])
            item_address.setFlags(Qt.ItemIsEnabled)
            item_value = QTableWidgetItem("{}".format(address['balance']))
            item_value.setFlags(Qt.ItemIsEnabled)
            table_addresses.setItem(col, 0, item_address)
            table_addresses.setItem(col, 1, item_value)
            col += 1

        table_addresses.verticalHeader().setVisible(False)
        table_addresses.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_addresses.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table_addresses.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table_addresses.resizeColumnsToContents()
        width_table = table_addresses.horizontalHeader().length() + table_addresses.verticalHeader().width() - 13
        table_addresses.setFixedSize(width_table,
                                     table_addresses.verticalHeader().length() + table_addresses.horizontalHeader().height() + 1)
        vbox_addresses.addWidget(table_addresses, alignment=Qt.AlignCenter)

        button_create_address = QPushButton("Create New Address")
        button_create_address.setFixedWidth(width_table)
        button_create_address.clicked.connect(self.do_create_address)
        vbox_addresses.addWidget(button_create_address, alignment=Qt.AlignCenter)

        vbox_addresses.addStretch(1)

        return vbox_addresses

    def init_send_ui(self):
        vbox_send = QVBoxLayout()
        label_heading = QLabel("Send Koin")
        label_heading.setFont(self.font_heading)
        vbox_send.addWidget(label_heading, alignment=Qt.AlignLeft)

        widget_send_form = QWidget()
        layout_send_form = QVBoxLayout()

        hbox_address = QHBoxLayout()
        label_address = QLabel("Address:")
        label_address.setFont(self.font_form)
        hbox_address.addWidget(label_address, alignment=Qt.AlignLeft)
        self.input_address = QLineEdit()
        self.input_address.setFixedWidth(200)
        hbox_address.addWidget(self.input_address, alignment=Qt.AlignRight)
        layout_send_form.addLayout(hbox_address)

        hbox_amount = QHBoxLayout()
        label_amount = QLabel("Amount:")
        label_amount.setFont(self.font_form)
        hbox_amount.addWidget(label_amount, alignment=Qt.AlignLeft)
        self.input_amount = QLineEdit()
        self.input_amount.setFixedWidth(200)
        hbox_amount.addWidget(self.input_amount, alignment=Qt.AlignRight)
        layout_send_form.addLayout(hbox_amount)

        hbox_description = QHBoxLayout()
        label_description = QLabel("Description:")
        label_description.setFont(self.font_form)
        hbox_description.addWidget(label_description, alignment=Qt.AlignLeft)
        self.input_description = QLineEdit()
        self.input_description.setFixedWidth(200)
        hbox_description.addWidget(self.input_description, alignment=Qt.AlignRight)
        layout_send_form.addLayout(hbox_description)

        button_send = QPushButton("Send")
        button_send.clicked.connect(self.do_send)
        layout_send_form.addWidget(button_send, alignment=Qt.AlignRight)

        widget_send_form.setLayout(layout_send_form)
        widget_send_form.setFixedWidth(350)
        vbox_send.addStretch(1)
        vbox_send.addWidget(widget_send_form, alignment=Qt.AlignCenter)
        vbox_send.addStretch(1)

        return vbox_send

    def init_history_ui(self):
        vbox_history = QVBoxLayout()
        label_heading = QLabel("Transaction History")
        label_heading.setFont(self.font_heading)
        vbox_history.addWidget(label_heading, alignment=Qt.AlignLeft)

        transactions = self.multichain.get_transactions()

        table_transactions = QTableWidget(len(transactions), 4)
        table_transactions.setHorizontalHeaderLabels(['Date', 'Description', 'Amount', 'Balance\n(after transaction)'])
        col = 0
        for transaction in transactions:
            item_date = QTableWidgetItem("{}".format(transaction['date']))
            item_date.setFlags(Qt.ItemIsEnabled)
            item_value = QTableWidgetItem("{}".format(transaction['amount']))
            item_value.setFlags(Qt.ItemIsEnabled)
            table_transactions.setItem(col, 0, item_date)
            table_transactions.setItem(col, 2, item_value)
            col += 1

        table_transactions.verticalHeader().setVisible(False)
        table_transactions.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_transactions.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table_transactions.resizeColumnsToContents()
        table_transactions.setFixedSize(
            table_transactions.horizontalHeader().length() + table_transactions.verticalHeader().width() - 11,
            400)
        vbox_history.addWidget(table_transactions, alignment=Qt.AlignCenter)

        vbox_history.addStretch(1)

        return vbox_history

    def do_create_address(self):
        self.multichain.create_address()

    def do_send(self):
        self.multichain.send(self.input_address.text(), self.input_amount.text(), self.input_description.text())
        self.input_address.setText('')
        self.input_amount.setText('')
        self.input_description.setText('')
