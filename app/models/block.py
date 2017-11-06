# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db

from .address import Address


log = logging.getLogger(__name__)


class Block(peewee.Model):
    """Blocks"""

    hash = peewee.BlobField(primary_key=True)
    time = peewee.DateTimeField()
    miner = peewee.ForeignKeyField(Address, related_name='mined_blocks')
    txcount = peewee.IntegerField()
    height = peewee.IntegerField()

    class Meta:
        database = data_db

    def __repr__(self):
        return "Block(h=%s, t=%s, txs=%s)" % (self.height, self.time, self.txcount)
