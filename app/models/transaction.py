# -*- coding: utf-8 -*-
import logging

from sqlalchemy import String, Column, Integer, ForeignKey, LargeBinary, exists

from app.models.db import data_db, data_base


log = logging.getLogger(__name__)


class Transaction(data_base):
    __tablename__ = "transactions"
    """Transactions"""

    txid = Column(String, primary_key=True)
    block = Column(LargeBinary, ForeignKey('blocks.hash'))
    pos_in_block = Column(Integer)

    class Meta:
        database = data_db

    def value_by_col(self, col): # todo: nie benutzt, weg?
        fn = self._meta.sorted_field_names[col]
        return getattr(self, fn)

    @staticmethod
    def create_if_not_exists(transaction):
        if not data_db().query(exists().where(Transaction.txid == transaction.txid)).scalar():
            data_db().add(transaction)
            data_db().commit()
