# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Float

from app.models.db import data_base

log = logging.getLogger(__name__)


class MyTransaction(data_base):
    __tablename__ = "my_transactions"

    PAYMENT, VOTE, MINING_REWARD, PUBLISH = "payment", "vote", "mining_reward", "publish"
    TRANSACTION_TYPES = PAYMENT, VOTE, MINING_REWARD, PUBLISH

    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE"), primary_key=True)
    amount = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8))
    tx_fee = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8))
    comment = Column(String)
    type = Column(Enum(*TRANSACTION_TYPES))
    balance = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8))

    def __repr__(self):
        return "MyTransaction(%s, %s)" % (self.txid, self.type)
