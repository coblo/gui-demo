# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db

from .address import Address


log = logging.getLogger(__name__)


class Block(peewee.Model):
    """Blocks"""

    # TODO: store hash as raw bytes in BlobField
    hash = peewee.CharField(primary_key=True)
    time = peewee.DateTimeField()
    miner = peewee.ForeignKeyField(Address, related_name='mined_blocks')
    txcount = peewee.IntegerField()
    height = peewee.IntegerField()

    class Meta:
        database = data_db

    def __repr__(self):
        return "Block(%s)" % self.height
