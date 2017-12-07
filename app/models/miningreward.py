# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from sqlalchemy import Column, String, ForeignKey, func

from app.models.db import data_base, data_db

log = logging.getLogger(__name__)


class MiningReward(data_base):
    __tablename__ = "mining_rewards"
    """Mining Rewards"""

    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE"), primary_key=True)
    address = Column(String)

    def __repr__(self):
        return "MiningReward(%s, %s)" % (self.txid, self.address)


    @staticmethod
    def last_mined(address):
        from app.models import Transaction, Block
        return data_db().query(Block.time).join(Transaction, MiningReward).filter(MiningReward.address == address)\
            .order_by(Block.time.desc()).first()

    @staticmethod
    def mined_last_24h():
        from app.models import Transaction, Block
        return data_db().query(MiningReward.address, func.count(MiningReward.txid)).join(Transaction, Block).filter(
            datetime.now() - timedelta(days=1) <= Block.time).group_by(MiningReward.address).all()