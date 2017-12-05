# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey

from app.models import Transaction, Block
from app.models.db import data_base, data_db

log = logging.getLogger(__name__)


class Timestamp(data_base):
    __tablename__ = "timestamps"

    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE"), primary_key=True)
    address = Column(String)
    hash = Column(String, index=True)
    comment = Column(String)

    def __repr__(self):
        return "(%s, %s)" % (self.txid, self.type)

    @staticmethod
    def get_timestamps_for_hash(hash_value: str) -> []:
        # The first table mentioned is in the FROM clause
        return (data_db().
                query(Block.time, Timestamp.address, Timestamp.comment).
                join(Transaction, Timestamp.txid == Transaction.txid).
                join(Timestamp, Block.hash == Transaction.block).
                filter(Timestamp.hash == hash_value)
                ).all()
