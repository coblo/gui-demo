# -*- coding: utf-8 -*-
import logging
from binascii import unhexlify

from sqlalchemy import LargeBinary, Column, DateTime, Integer, exists

from app.models.db import data_db, data_base

log = logging.getLogger(__name__)


class Block(data_base):

    __tablename__ = "blocks"
    """Blocks"""

    hash = Column(LargeBinary, primary_key=True)
    mining_time = Column(DateTime)
    height = Column(Integer)

    class Meta:
        database = data_db

    def __repr__(self):
        return "Block(h=%s, t=%s, txs=%s)" % (self.height, self.mining_time, self.txcount)

    @staticmethod
    def block_exists(data_db, block_hash):
        return data_db.query(exists().where(Block.hash == unhexlify(block_hash))).scalar()

