#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Elements for PyQt"""
from PyQt5.QtWidgets import QFrame


def get_hline():
    hline = QFrame()
    hline.setFrameShape(QFrame.HLine)
    return hline

def get_vline():
    hline = QFrame()
    hline.setFrameShape(QFrame.VLine)
    return hline