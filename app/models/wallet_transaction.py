# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Float, Integer, exists

from app.models.db import data_base

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
    def wallet_transaction_in_db(data_db, txid):
        return data_db.query(exists().where(WalletTransaction.txid == txid)).scalar()

    @staticmethod
    def compute_balances(data_db) -> bool:
        from app.models import Block, Transaction
        first_unknown_balance = (
            data_db.query(WalletTransaction, Block.mining_time).
            join(Transaction, Block).
            filter(WalletTransaction.balance.is_(None)).
            order_by(Block.mining_time.asc())
        ).first()
        if first_unknown_balance is not None:
            last_valid_balance = data_db.query(WalletTransaction.balance).join(Transaction, Block) \
                .filter(WalletTransaction.balance.isnot(None)).order_by(Block.mining_time.desc()).first()
            if not last_valid_balance:
                last_valid_balance = 0
            else:
                last_valid_balance = last_valid_balance[0]
            txs_with_unknown_balance = data_db.query(WalletTransaction).join(Transaction, Block) \
                .filter(Block.mining_time >= first_unknown_balance.mining_time).order_by(Block.mining_time.asc()).all()
            for tx in txs_with_unknown_balance:
                last_valid_balance += tx.amount
                tx.balance = last_valid_balance

        return bool(first_unknown_balance)

    @staticmethod
    def get_wallet_history(data_db):
        from app.models import Block, Transaction
        return data_db.query(
            WalletTransaction.tx_type,
            Block.mining_time,
            WalletTransaction.comment,
            WalletTransaction.amount,
            WalletTransaction.balance,
            WalletTransaction.txid,
            Transaction.pos_in_block
        ).outerjoin(Transaction, Block).order_by(Block.mining_time.desc()).all()
