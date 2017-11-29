# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Integer

from app.models import Transaction, Block
from app.models.db import data_base

log = logging.getLogger(__name__)


class Timestamp(data_base):
    __tablename__ = "timestamps"

    timestamp_id = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    pos_in_tx = Column(Integer)
    address = Column(String)
    hash = Column(String, index=True)
    comment = Column(String)

    def __repr__(self):
        return "(%s, %s)" % (self.txid, self.type)

    @staticmethod
    def get_timestamps_for_hash(data_db, hash_value: str) -> []:
        # The first table mentioned is in the FROM clause
        return (data_db.
                query(Block.mining_time, Timestamp.address, Timestamp.comment).
                join(Transaction, Timestamp.txid == Transaction.txid).
                join(Timestamp, Block.hash == Transaction.block).
                filter(Timestamp.hash == hash_value).
                order_by(Block.height.asc(), Transaction.pos_in_block.asc(), Timestamp.pos_in_tx.asc())
                ).all()

    @staticmethod
    def get_timestamps_for_address(data_db, address: str):
        result = data_db.query(Block.time, Timestamp.hash, Timestamp.comment).join(Transaction, Timestamp).filter(Timestamp.address == address).all()

        return result

