# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Float, Integer, exists

from app.models.db import data_base, data_db

log = logging.getLogger(__name__)


class WalletTransaction(data_base):
    __tablename__ = "wallet_transactions"
    """Wallet Transactions"""

    PAYMENT, VOTE, MINING_REWARD, PUBLISH, CREATE = "payment", "vote", "mining_reward", "publish", "create"
    TRANSACTION_TYPES = PAYMENT, VOTE, MINING_REWARD, PUBLISH, CREATE

    wallet_txid = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    amount = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8))
    comment = Column(String)
    tx_type = Column(Enum(*TRANSACTION_TYPES))
    balance = Column(Float(asdecimal=True, precision=17, decimal_return_scale=8), nullable=True)

    def __repr__(self):
        return "MyTransaction(%s, %s)" % (self.txid, self.tx_type)

    @staticmethod
    def wallet_transaction_in_db(txid):
        return data_db().query(exists().where(WalletTransaction.txid == txid)).scalar()

    @staticmethod
    def compute_balances():
        from app.models import Block, Transaction
        first_unknown_balance = data_db().query(WalletTransaction, Block.time).join(Transaction, Block)\
            .filter(WalletTransaction.balance == None).order_by(Block.time.asc()).first()
        if first_unknown_balance is not None:
            last_valid_balance = data_db().query(WalletTransaction.balance).join(Transaction, Block)\
            .filter(WalletTransaction.balance != None).order_by(Block.time.desc()).first()
            if not last_valid_balance:
                last_valid_balance = 0
            else:
                last_valid_balance = last_valid_balance[0]
            txs_with_unknown_balance = data_db().query(WalletTransaction).join(Transaction, Block)\
                .filter(Block.time >= first_unknown_balance.time).order_by(Block.time.asc()).all()
            for tx in txs_with_unknown_balance:
                last_valid_balance += tx.amount
                tx.balance = last_valid_balance
            data_db().commit()

    @staticmethod
    def get_wallet_history():
        from app.models import Block, Transaction
        return data_db().query(WalletTransaction, Block.time).join(Transaction, Block).order_by(Block.time.desc()).all()
