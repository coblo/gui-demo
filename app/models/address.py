# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db


log = logging.getLogger(__name__)


class Address(peewee.Model):
    """Addresses"""

    address = peewee.CharField(primary_key=True)
    alias = peewee.CharField(unique=True, null=True)

    def __repr__(self):
        return 'Address(%s, %s)' % (self.address, self.alias)

    class Meta:
        database = data_db
