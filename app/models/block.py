# -*- coding: utf-8 -*-
import logging
from sqlalchemy import LargeBinary, Column, DateTime, ForeignKey, String, Integer

from app.models.db import data_db, data_base

from .address import Address


log = logging.getLogger(__name__)


class Block(data_base):

    __tablename__ = "blocks"
    """Blocks"""

    hash = Column(LargeBinary, primary_key=True)
    time = Column(DateTime)
    height = Column(Integer)

    class Meta:
        database = data_db

    def __repr__(self):
        return "Block(h=%s, t=%s, txs=%s)" % (self.height, self.time, self.txcount)

    @classmethod
    def multi_tx_blocks(cls): # todo: wahrscheinlich ab jetzt unnötig, mal gucken
        # return cls.select().where(cls.txcount > 1)
        pass
