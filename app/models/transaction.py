# -*- coding: utf-8 -*-
import logging

from sqlalchemy import String, Column, Integer, ForeignKey, LargeBinary, exists

from app.models.db import data_base

log = logging.getLogger(__name__)


class Transaction(data_base):
    __tablename__ = "transactions"
    """Transactions"""

    txid = Column(String, primary_key=True)
    block = Column(LargeBinary, ForeignKey('blocks.hash', deferrable=True, ondelete="CASCADE", initially="DEFERRED"), nullable=True)
    pos_in_block = Column(Integer)

    def __repr__(self):
        return "Transaction(%s)" % (self.txid)

    @staticmethod
    def create_if_not_exists(data_db, transaction):
        old_transaction = data_db.query(Transaction).filter(Transaction.txid == transaction.txid).first()
        if old_transaction is None:
            data_db.add(transaction)
        elif old_transaction.block is None and transaction.block is not None:  # transaction was unconfirmed before
            old_transaction.block = transaction.block
            old_transaction.pos_in_block = transaction.pos_in_block

    @staticmethod
    def transaction_in_db(data_db,txid):
        return data_db.query(exists().where(Transaction.txid == txid)).scalar()
