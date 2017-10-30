# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db


log = logging.getLogger(__name__)


class Address(peewee.Model):
    """Addresses"""

    address = peewee.CharField(primary_key=True)
    alias = peewee.CharField(default='')

    class Meta:
        database = data_db
