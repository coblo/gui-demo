# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db

from .address import Address


log = logging.getLogger(__name__)


class Permission(peewee.Model):
    """Address permissions"""

    ISSUE, CREATE, MINE, ADMIN = 'issue', 'create', 'mine', 'admin'
    PERM_TYPES = ISSUE, CREATE, MINE, ADMIN

    address = peewee.ForeignKeyField(Address, related_name='permissions')
    perm_type = peewee.CharField(choices=PERM_TYPES)
    start_block = peewee.IntegerField()
    end_block = peewee.IntegerField()

    class Meta:
        database = data_db
        primary_key = peewee.CompositeKey('address', 'perm_type')