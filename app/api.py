# -*- coding: utf-8 -*-
"""High level api functions for reading and writing blockchain data."""
from typing import Optional, NewType
from decimal import Decimal
from app.enums import Permission


TxId = NewType('TxID', str)
Form = NewType('Form', dict)


# TODO define and implement highlevel api


def pay(to_address: str, amount: Decimal, comment: str, fee: Decimal=Decimal('0.0001')) -> Optional(TxId):
    pass


def register_alias(alias: str) -> Optional(TxId):
    pass


def apply_for(perm: Permission, form: Form) -> Optional(TxId):
    pass
