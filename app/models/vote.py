# -*- coding: utf-8 -*-
import logging
from datetime import timedelta, datetime

from sqlalchemy import Column, String, ForeignKey, Enum, Integer, func

from app.enums import PermTypes
from app.models.db import data_base, data_db

log = logging.getLogger(__name__)


class Vote(data_base):
    __tablename__ = "votes"

    vote_id = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    from_address = Column(String)
    to_address = Column(String)
    start_block = Column(Integer)
    end_block = Column(Integer)
    perm_type = Column(Enum(PermTypes))

    def __repr__(self):
        return "Vote(%s, %s, %s, %s)" % (self.txid, self.from_address, self.to_address, self.perm_type)

    @staticmethod
    def last_voted(address):
        from app.models import Transaction, Block
        return data_db().query(Block.time).join(Transaction, Vote).filter(Vote.from_address == address)\
            .order_by(Block.time.desc()).first()

    @staticmethod
    def voted_last_24h():
        from app.models import Transaction, Block
        return data_db().query(Vote.from_address, func.count(Vote.txid)).join(Transaction, Block).filter(
            datetime.now() - timedelta(days=1) <= Block.time).group_by(Vote.from_address).all()