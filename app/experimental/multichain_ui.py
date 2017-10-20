#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""MultiChain Minimal Gui"""
import codecs
import sys
from bitcoinrpc.authproxy import AuthServiceProxy
from datetime import datetime
from functools import partial

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QPlainTextEdit, QSizePolicy, \
    QScrollArea, QComboBox, QFrame, QLabel, QLineEdit, QTextEdit, QDialog

from app.experimental.iscc_ui import Iscc
from config import rpcuser, rpcpassword


class Multichain(QWidget):
    def __init__(self):
        super().__init__()
        self.connection = AuthServiceProxy(
            "http://%s:%s@127.0.0.1:8374" % (rpcuser, rpcpassword))
        self.heading_font = QFont("Arial", 14)
        self.initUI()

    def initUI(self):
        self.log_window = QPlainTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # streams
        stream_vbox = QVBoxLayout()
        stream_header = QLabel("Streams:")
        stream_header.setFont(self.heading_font)
        stream_vbox.addWidget(stream_header)
        stream_vbox.addLayout(self.init_stream_window())
        stream_vbox.addStretch(1)

        # logwindow and buttons
        log_vbox = QVBoxLayout()
        log_header = QLabel("Log Window:")
        log_header.setFont(self.heading_font)
        log_vbox.addWidget(log_header)
        log_vbox.addWidget(self.log_window)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        btn_generate_iscc = QPushButton("Generate ISCC")
        btn_generate_iscc.clicked.connect(self.do_generate_iscc)
        hbox.addWidget(btn_generate_iscc)
        btn_getbalance = QPushButton("Get Balance")
        btn_getbalance.clicked.connect(self.do_getbalance)
        hbox.addWidget(btn_getbalance)
        log_vbox.addLayout(hbox)

        # list of blocks
        block_vbox = QVBoxLayout()
        block_header = QLabel("Blocks:")
        block_header.setFont(self.heading_font)
        block_vbox.addWidget(block_header)
        block_vbox.addWidget(self.init_block_window())

        # main window
        main_hbox = QHBoxLayout()
        main_hbox.addLayout(stream_vbox)
        main_hbox.addLayout(log_vbox)
        main_hbox.addLayout(block_vbox)

        self.setLayout(main_hbox)
        self.setGeometry(500, 200, 960, 640)
        self.setWindowTitle('Content Blockchain')
        self.show()

    def init_stream_window(self):
        vbox = QVBoxLayout()
        self.stream_combo = QComboBox()
        streams = self.connection.liststreams()
        for stream in streams:
            if stream['subscribed']:
                self.stream_combo.addItem(stream['name'])
        self.selected_stream = self.stream_combo.currentText()
        self.stream_combo.currentIndexChanged.connect(self.do_stream_change)
        vbox.addWidget(self.stream_combo)
        vbox.addWidget(self.init_stream_items(self.selected_stream))

        key_hbox = QHBoxLayout()
        key_hbox.addWidget(QLabel("Key:  "))
        self.publish_key_input = QLineEdit()
        key_hbox.addWidget(self.publish_key_input)
        vbox.addLayout(key_hbox)

        value_hbox = QHBoxLayout()
        value_hbox.addWidget(QLabel("Data:"))
        self.publish_value_input = QTextEdit()
        value_hbox.addWidget(self.publish_value_input)
        vbox.addLayout(value_hbox)

        btn_publish = QPushButton("Publish")
        btn_publish.clicked.connect(self.do_publish)
        vbox.addWidget(btn_publish)
        return vbox

    def init_block_window(self):
        blocks = self.connection.listblocks([x for x in range(0, self.connection.getblockcount() + 1)])
        blocks.reverse()
        vbox = QVBoxLayout()
        for block in blocks:
            btn_block = QPushButton("Block {}".format(block['height']))
            btn_block.clicked.connect(partial(self.do_getblockinfo, btn_block.text()))
            vbox.addWidget(btn_block)
        tmp = QWidget()
        tmp.setLayout(vbox)
        scrollarea = QScrollArea()
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollarea.setWidget(tmp)
        scrollarea.setAlignment(Qt.AlignHCenter)
        scrollarea.setFixedWidth(125)
        return scrollarea

    def init_stream_items(self, stream):
        self.stream_item_list = QScrollArea()
        self.do_change_stream_items(self.selected_stream)
        return self.stream_item_list

    def do_generate_iscc(self):
        self.iscc_dialog = QDialog()
        tmp = QVBoxLayout()
        tmp.addWidget(Iscc(self))
        self.iscc_dialog.setLayout(tmp)
        self.iscc_dialog.setGeometry(550, 250, 860, 540)
        self.iscc_dialog.setWindowTitle('Generate ISCC')
        self.iscc_dialog.exec_()

    def do_getbalance(self):
        text = 'Balance: {} Coins'.format(self.connection.getbalance())
        self.log_window.appendPlainText(text.strip())

    def do_getblockinfo(self, button_name):
        height = button_name.split("Block ")[1]
        block = self.connection.getblock(height)
        text = 'Block: {}\n'.format(height)
        text += 'Hash: {}\n'.format(block['hash'])
        text += 'Miner: {}\n'.format(self.get_node_alias(block['miner']))
        text += 'Time: {}\n'.format(datetime.fromtimestamp(block['time']))
        self.log_window.appendPlainText("\n{}\n".format(text.strip()))

    def do_stream_change(self, index):
        new_stream = self.stream_combo.currentText()
        self.selected_stream = new_stream
        self.do_change_stream_items(new_stream)

    def do_change_stream_items(self, stream):
        items = self.connection.liststreamitems(stream)
        main_vbox = QVBoxLayout()
        for item in items:
            vbox = QVBoxLayout()
            vbox.addWidget(QLabel("Key: {}".format(item['key'])))
            vbox.addWidget(QLabel("Data: {}".format(codecs.decode(item['data'], 'hex').decode('ascii'))))
            vbox.addWidget(QLabel("Publishers: {}".format(", ".join(self.get_node_alias(item['publishers'])))))
            if 'blocktime' in item:
                vbox.addWidget(QLabel("Time: {}".format(datetime.fromtimestamp(item['blocktime']))))
            main_vbox.addLayout(vbox)
            if item != items[-1]:
                bottom_line = QFrame()
                bottom_line.setGeometry(QRect(320, 150, 118, 3))
                bottom_line.setFrameShape(QFrame.HLine)
                bottom_line.setFrameShadow(QFrame.Sunken)
                main_vbox.addWidget(bottom_line)
        tmp = QWidget()
        tmp.setFixedWidth(382)
        tmp.setLayout(main_vbox)
        self.stream_item_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.stream_item_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.stream_item_list.setWidget(tmp)
        self.stream_item_list.setFixedHeight(310)

    def do_publish(self):
        data = codecs.encode(self.publish_value_input.toPlainText().encode('utf-8'), 'hex')
        if len(self.publish_key_input.text()) > 0 and len(self.publish_value_input.toPlainText()) > 0:
            self.connection.publish(self.selected_stream, self.publish_key_input.text(), data.decode('ascii'))
            self.log_window.appendPlainText("\nStream: {}".format(self.selected_stream))
            self.log_window.appendPlainText("Key: {}".format(self.publish_key_input.text()))
            self.log_window.appendPlainText("Data: {}".format(self.publish_value_input.toPlainText()))
            self.do_change_stream_items(self.selected_stream)
            self.publish_key_input.setText('')
            self.publish_value_input.setText('')
        else:
            self.log_window.appendPlainText("Please give a key and data")

    def get_node_alias(self, address):
        if type(address) is list:
            return [self.get_node_alias(address_entry) for address_entry in address]
        alias = address
        alias_list = self.connection.liststreampublisheritems('alias', address)
        for alias_entry in alias_list:
            already_used = False
            key = alias_entry['key']
            time = alias_entry['blocktime']
            for other_alias in self.connection.liststreamkeyitems('alias', key):
                if other_alias['blocktime'] < time:
                    already_used = True
            if not already_used:
                alias = key
        return alias

    def pass_iscc(self, key, value):
        self.publish_key_input.setText(key)
        self.publish_value_input.setText(value)
        stream_index = self.stream_combo.findText('test_iscc', Qt.MatchFixedString)
        if stream_index >= 0:
            self.stream_combo.setCurrentIndex(stream_index)
        self.iscc_dialog.done(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Multichain()
    sys.exit(app.exec_())
