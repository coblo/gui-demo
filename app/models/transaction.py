# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db


log = logging.getLogger(__name__)


class Transaction(peewee.Model):
    """Wallet transactions"""

    datetime = peewee.DateTimeField()
    comment = peewee.CharField()
    amount = peewee.DecimalField(max_digits=17, decimal_places=8)
    balance = peewee.DecimalField(max_digits=17, decimal_places=8)
    confirmations = peewee.SmallIntegerField()
    txid = peewee.CharField(primary_key=True)

    class Meta:
        database = data_db

    def value_by_col(self, col):
        fn = self._meta.sorted_field_names[col]
        return getattr(self, fn)
