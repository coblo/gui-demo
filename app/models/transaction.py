# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db


log = logging.getLogger(__name__)


class Transaction(peewee.Model):
    """Wallet transactions"""

    txid = peewee.CharField(primary_key=True)

    class Meta:
        database = data_db
