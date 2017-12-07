# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Float, Integer, exists

from app.models.db import data_base, data_db

log = logging.getLogger(__name__)


class WalletTransaction(data_base):
    __tablename__ = "wallet_transactions"
    """Wallet Transactions"""

    PAYMENT, VOTE, MINING_REWARD, PUBLISH, TX_FEE, CREATE = "payment", "vote", "mining_reward", "publish", "tx_fee", "create"
    TRANSACTION_TYPES = PAYMENT, VOTE, MINING_REWARD, PUBLISH, TX_FEE, CREATE

    wallet_txid = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    amount = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8))
    tx_fee = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8))
    comment = Column(String)
    tx_type = Column(Enum(*TRANSACTION_TYPES))
    balance = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8), nullable=True)

    def __repr__(self):
        return "MyTransaction(%s, %s)" % (self.txid, self.tx_type)

    @staticmethod
    def wallet_transaction_in_db(txid):
        return data_db().query(exists().where(WalletTransaction.txid == txid)).scalar()
