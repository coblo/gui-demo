# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db
from app.enums import PermType

from .address import Address


log = logging.getLogger(__name__)


class Permission(peewee.Model):
    """Address permissions"""

    MAX_END_BLOCK = 4294967295

    address = peewee.ForeignKeyField(Address, related_name='permissions')
    perm_type = peewee.CharField(choices=PermType)
    start_block = peewee.IntegerField()
    end_block = peewee.IntegerField()

    class Meta:
        database = data_db
        primary_key = peewee.CompositeKey('address', 'perm_type')

    def __repr__(self):
        return "Permission(%s, %s, %s, %s)" % (
            self.address_id[:4], self.perm_type, self.start_block, self.end_block
        )

    @staticmethod
    def validators():
        return Permission.select().where(
            Permission.perm_type == PermType.MINE,
            Permission.start_block == 0,
            Permission.end_block == Permission.MAX_END_BLOCK,
        )

    @staticmethod
    def guardians():
        return Permission.select().where(
            Permission.perm_type == PermType.ADMIN,
            Permission.start_block == 0,
            Permission.end_block == Permission.MAX_END_BLOCK,
        )

    @staticmethod
    def num_validators():
        return Permission.validators().count()

    @staticmethod
    def num_guardians():
        return Permission.guardians().count()

