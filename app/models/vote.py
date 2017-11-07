# -*- coding: utf-8 -*-
import logging
import peewee
from app.models import Address
from app.models.db import data_db


log = logging.getLogger(__name__)


class Vote(peewee.Model):

    txid = peewee.CharField()
    from_address = peewee.ForeignKeyField(Address, related_name='votes_given')
    to_address = peewee.ForeignKeyField(Address, related_name='votes_received')
    time = peewee.DateTimeField()

    class Meta:
        database = data_db

    def __repr__(self):
        return "Vote(%s, %s, %s)" % (self.time, self.from_address, self.to_address)
