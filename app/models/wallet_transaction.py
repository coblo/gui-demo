# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Float, Integer, exists
from sqlalchemy.event import listens_for

from app.signals import signals
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
        first_unknown_balance = data_db().query(WalletTransaction, Block.time).join(Transaction, Block) \
            .filter(WalletTransaction.balance == None).order_by(Block.time.asc()).first()
        if first_unknown_balance is not None:
            last_valid_balance = data_db().query(WalletTransaction.balance).join(Transaction, Block) \
                .filter(WalletTransaction.balance != None).order_by(Block.time.desc()).first()
            if not last_valid_balance:
                last_valid_balance = 0
            else:
                last_valid_balance = last_valid_balance[0]
            txs_with_unknown_balance = data_db().query(WalletTransaction).join(Transaction, Block) \
                .filter(Block.time >= first_unknown_balance.time).order_by(Block.time.asc()).all()
            for tx in txs_with_unknown_balance:
                last_valid_balance += tx.amount
                tx.balance = last_valid_balance
            data_db().commit()

    @staticmethod
    def get_wallet_history():
        from app.models import Block, Transaction
        transactions = []
        for tx in data_db().query(WalletTransaction, Block.time).join(Transaction, Block).order_by(Block.time.desc()).all():
            transactions.append({
                'tx_type': tx.WalletTransaction.tx_type,
                'time': tx.time,
                'comment': tx.WalletTransaction.comment,
                'amount': tx.WalletTransaction.amount,
                'balance': tx.WalletTransaction.balance,
                'txid': tx.WalletTransaction.wallet_txid
            })
        for tx in data_db().query(WalletTransaction).filter(WalletTransaction.txid == None).all():
            transactions.append({
                'tx_type': tx.tx_type,
                'time': None,
                'comment': tx.comment,
                'amount': tx.amount,
                'balance': tx.balance,
                'txid': tx.wallet_txid
            })
        return transactions

    @staticmethod
    def delete_unconfirmed_wallet_txs():
        for tx in data_db().query(WalletTransaction).filter(WalletTransaction.txid == None).all():
            data_db().delete(tx)


def transaction_for_history(wallet_transaction):
    transaction = {
        'tx_type': wallet_transaction.tx_type,
        'comment': wallet_transaction.comment,
        'amount': wallet_transaction.amount,
        'balance': wallet_transaction.balance,
        'txid': wallet_transaction.wallet_txid
    }
    if wallet_transaction.txid is None:  # tx is unconfirmed
        transaction['time'] = None
    else:
        from app.models import Block, Transaction
        tx = data_db().query(WalletTransaction, Block.time).join(Transaction, Block) \
            .filter(WalletTransaction.txid == wallet_transaction.txid).first()
        transaction['time'] = None if tx is None else tx.time
    return transaction

@listens_for(WalletTransaction, "after_insert")
def after_insertion(mapper, connection, wallet_transaction):
    signals.wallet_transaction_inserted.emit(transaction_for_history(wallet_transaction))

@listens_for(WalletTransaction, "after_update")
def after_update(mapper, connection, wallet_transaction):
    signals.wallet_transaction_updated.emit(transaction_for_history(wallet_transaction))