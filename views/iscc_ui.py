#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""ISCC Minimal Gui"""
import codecs
import json
import sys

from bitcoinrpc.authproxy import AuthServiceProxy

from iscclib.meta import MetaID
from iscclib.text import TextID
from iscclib.data import DataID
from iscclib.instance import InstanceID

from config import rpcuser, rpcpassword

import tika

tika.initVM()
from tika import parser

from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, \
    QLineEdit, QDialog, QScrollArea


class Iscc(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.heading_font = QFont("Arial", 14)
        self.label_width = 50
        self.initUI()

    def initUI(self):
        main_vbox = QVBoxLayout()

        title_hbox = QHBoxLayout()
        title_label = QLabel("Title:")
        title_label.setFixedWidth(self.label_width)
        title_hbox.addWidget(title_label)
        self.title_input = QLineEdit()
        self.title_input.setFocus()
        title_hbox.addWidget(self.title_input)
        main_vbox.addLayout(title_hbox)

        file_hbox = QHBoxLayout()
        file_label = QLabel("File:")
        file_label.setFixedWidth(self.label_width)
        file_hbox.addWidget(file_label)
        btn_select_file = QPushButton("Select File")
        btn_select_file.clicked.connect(self.do_select_file)
        file_hbox.addWidget(btn_select_file)
        self.file_path_label = QLabel()
        file_hbox.addWidget(self.file_path_label)
        main_vbox.addLayout(file_hbox)
        self.btn_show_content = QPushButton("Show Content")
        self.btn_show_content.clicked.connect(self.do_show_content)
        self.btn_show_content.setHidden(True)
        file_hbox.addWidget(self.btn_show_content)

        btn_generate = QPushButton("Generate ISCC")
        btn_generate.clicked.connect(self.do_generate)
        main_vbox.addWidget(btn_generate)

        self.iscc_label = QLabel()
        self.iscc_label.setAlignment(Qt.AlignCenter)
        main_vbox.addWidget(self.iscc_label)

        self.btn_continue = QPushButton("Continue")
        self.btn_continue.clicked.connect(self.do_continue)
        self.btn_continue.setHidden(True)
        main_vbox.addWidget(self.btn_continue)

        self.setLayout(main_vbox)
        self.setGeometry(500, 200, 960, 640)
        self.setWindowTitle('Generate ISCC')
        self.show()

    def do_generate(self):
        if len(self.title_input.text()) == 0:
            self.iscc_label.setText('Please give a title!')
            return
        if len(self.file_path_label.text()) == 0:
            self.iscc_label.setText('Please select a file!')
            return
        meta_text = self.title_input.text()
        meta = MetaID.from_meta(title=meta_text, bits=64)
        content_text = self.extract_file()
        content = TextID.from_text(content_text, bits=64)
        path = self.file_path_label.text()
        with open(path, 'rb') as file:
            data = DataID.from_stream(file)
        with open(path, 'rb') as file:
            instance = InstanceID.from_data(file.read())
        self.iscc = '{}-{}-{}-{}'.format(meta, content, data, instance)
        bitstring = meta.bitstring + '\n' + content.bitstring + '\n' + data.bitstring + '\n' + instance.bitstring
        self.iscc_label.setText('{} - {} - {} - {}\n\n{}'.format(meta, content, data, instance, bitstring))
        self.btn_continue.setHidden(not self.check_conflicts())

    def do_select_file(self):
        path = QFileDialog.getOpenFileName()
        self.file_path_label.setText(path[0])
        self.btn_show_content.setHidden(False)

    def do_show_content(self):
        content = self.extract_file()
        content_dialog = QDialog()
        text_label = QLabel(content)
        scrollarea = QScrollArea()
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollarea.setWidget(text_label)
        v_box = QVBoxLayout()
        v_box.addWidget(scrollarea)
        content_dialog.setLayout(v_box)
        content_dialog.setWindowTitle('Extracted Content')
        content_dialog.exec_()


    def extract_file(self):
        path = self.file_path_label.text()
        parsed_file = parser.from_file(path)
        content = parsed_file["content"].strip()
        return content

    def do_continue(self):
        meta_data = {'title': self.title_input.text()}
        value = json.dumps(meta_data)
        self.main_window.pass_iscc(self.iscc, value)

    def check_conflicts(self):
        has_conflicts = False
        heading_font = QFont("Arial", 10)
        dialog = QDialog()
        connection = AuthServiceProxy(
            "http://%s:%s@127.0.0.1:8374" % (rpcuser, rpcpassword))

        v_box = QVBoxLayout()

        same_iscc = connection.liststreamkeyitems('test_iscc', self.iscc)
        if len(same_iscc) > 0:
            heading = QLabel("Same ISCC:")
            heading.setFont(heading_font)
            v_box.addWidget(heading)
            has_conflicts = True
            for iscc_entry in same_iscc:
                v_box.addWidget(QLabel("Key: {}".format(iscc_entry['key'])))
                v_box.addWidget(QLabel("Data: {}".format(codecs.decode(iscc_entry['data'], 'hex').decode('ascii'))))
                v_box.addWidget(QLabel("Publishers: {}".format(", ".join(self.get_node_alias(iscc_entry['publishers'])))))

        names = ['Meta', 'Content', 'Data', 'Instance']
        conflicts = [list(), list(), list(), list()]
        other_iscc = connection.liststreamitems('test_iscc')
        for iscc in other_iscc:
            key = iscc['key']
            if key != self.iscc:
                for i in range(4):
                    if key.split('-')[i] == self.iscc.split('-')[i]:
                        conflicts[i].append(key)
        for i, conflict_items in enumerate(conflicts):
            if len(conflict_items) > 0:
                has_conflicts = True
                heading = QLabel("Conflicts in {}-ID:".format(names[i]))
                heading.setFont(heading_font)
                v_box.addWidget(heading)
                for conflict_key in conflict_items:
                    for iscc_entry in connection.liststreamkeyitems('test_iscc', conflict_key):
                        v_box.addWidget(QLabel("Key: {}".format(iscc_entry['key'])))
                        v_box.addWidget(QLabel("Data: {}".format(codecs.decode(iscc_entry['data'], 'hex').decode('ascii'))))
                        v_box.addWidget(QLabel("Publishers: {}".format(", ".join(self.get_node_alias(iscc_entry['publishers'])))))

        if has_conflicts:
            tmp = QWidget()
            tmp.setLayout(v_box)
            scrollarea = QScrollArea()
            scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollarea.setWidget(tmp)
            main_v_box = QVBoxLayout()
            main_v_box.addWidget(scrollarea)

            dialog.setLayout(main_v_box)
            dialog.setWindowTitle('Conflicts')
            dialog.exec_()
            return False
        else:
            return True

    def get_node_alias(self, address):
        connection = AuthServiceProxy(
            "http://%s:%s@127.0.0.1:8374" % (rpcuser, rpcpassword))
        if type(address) is list:
            return [self.get_node_alias(address_entry) for address_entry in address]
        alias = address
        alias_list = connection.liststreampublisheritems('alias', address)
        for alias_entry in alias_list:
            already_used = False
            key = alias_entry['key']
            time = alias_entry['blocktime']
            for other_alias in connection.liststreamkeyitems('alias', key):
                if other_alias['blocktime'] < time:
                    already_used = True
            if not already_used:
                alias = key
        return alias




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Iscc()
    sys.exit(app.exec_())
