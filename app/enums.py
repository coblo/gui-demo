# -*- coding: utf-8 -*-
"""Enum constants"""
import enum

ISSUE, CREATE, MINE, ADMIN = 'issue', 'create', 'mine', 'admin'
class PermTypes(enum.Enum):
    issue = 0
    create = 1
    mine = 2
    admin = 3
