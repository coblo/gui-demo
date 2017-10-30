# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db

from .address import Address


log = logging.getLogger(__name__)


class Block(peewee.Model):
    """Blocks"""

    time = peewee.DateTimeField()
    miner = peewee.ForeignKeyField(Address, related_name='mined_blocks')
    txcount = peewee.IntegerField()
    hash = peewee.CharField(primary_key=True)
    height = peewee.IntegerField()


    class Meta:
        database = data_db
