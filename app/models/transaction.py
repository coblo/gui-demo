# -*- coding: utf-8 -*-
import logging

from sqlalchemy import String, Column, Integer, ForeignKey, LargeBinary, exists

from app.models.db import data_db, data_base


log = logging.getLogger(__name__)


class Transaction(data_base):
    __tablename__ = "transactions"
    """Transactions"""

    txid = Column(String, primary_key=True)
    block = Column(LargeBinary, ForeignKey('blocks.hash'), nullable=True)
    pos_in_block = Column(Integer)

    def __repr__(self):
        return "Transaction(%s)" % (self.txid)

    @staticmethod
    def create_if_not_exists(transaction):
        old_transaction = data_db().query(Transaction).filter(Transaction == transaction.txid).first()
        if old_transaction is None:
            data_db().add(transaction)
            data_db().commit()
        elif old_transaction.block is None: #transaction was unconfirmed before
            old_transaction.block = transaction.block
            old_transaction.pos_in_block = transaction.pos_in_block
            data_db().commit()


    @staticmethod
    def transaction_in_db(txid):
        return data_db().query(exists().where(Transaction.txid == txid)).scalar()