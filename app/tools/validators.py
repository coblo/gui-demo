# -*- coding: utf-8 -*-
"""Input Validation Classes"""
import re
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QValidator
from app.tools.address import address_valid


class AddressValidator(QValidator):

    min_length = 26
    max_length = 55
    symbols = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    internal_send = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def validate(self, input_str, position=0):
        for c in input_str:
            if c not in self.symbols:
                return QValidator.Invalid, input_str, position

        if self.max_length < len(input_str) < self.min_length:
            return QValidator.Intermediate, input_str, position

        if address_valid(input_str):
            return QValidator.Acceptable, input_str, position

        return QValidator.Intermediate, input_str, position


username_regex = re.compile(r"""
    ^                  # beginning of string
    (?!_$)             # no only _
    (?![-.])           # no - or . at the beginning
    (?!.*[_.-]{2})     # no __ or _. or ._ or .. or -- inside
    [a-z0-9_.-]{3,30}  # allowed characters (between 3 and 30)
    (?<![.-])          # no - or . at the end
    $                  # end of string
    """, re.X)


def is_valid_username(username):
    if not re.match(username_regex, username):
        return False
    else:
        return True
