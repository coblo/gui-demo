# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Integer

from app.models.db import data_base
from app.enums import PermTypes

log = logging.getLogger(__name__)


class Vote(data_base):
    __tablename__ = "votes"

    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE"), primary_key=True)
    from_address = Column(String)
    to_address = Column(String)
    start_block = Column(Integer, primary_key=True)
    end_block = Column(Integer, primary_key=True)
    perm_type = Column(Enum(PermTypes), primary_key=True)


    def __repr__(self):
        return "Vote(%s, %s, %s, %s)" % (self.txid, self.from_address, self.to_address, self.perm_type)
