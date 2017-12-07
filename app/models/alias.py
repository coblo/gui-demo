# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Integer

from app.models.db import data_base, data_db

log = logging.getLogger(__name__)


class Alias(data_base):
    __tablename__ = "alias"
    """Alias Changes"""

    alias_id = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    address = Column(String)
    alias = Column(String)

    def __repr__(self):
        return "Alias(%s, %s, %s)" % (self.txid, self.address, self.alias)

    @staticmethod
    def get_aliases() -> String:
        from app.models import Block, Transaction
        alias_list = {}
        for alias_entry in data_db().query(Alias, Block).join(Transaction, Block).order_by(Block.time.desc()).all():
            if alias_entry.Alias.address in alias_list.keys() or alias_entry.Alias.alias in alias_list.values():
                continue
            alias_list[alias_entry.Alias.address] = alias_entry.Alias.alias
        return alias_list
