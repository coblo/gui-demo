# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey

from app.models.db import data_base

log = logging.getLogger(__name__)


class MiningReward(data_base):
    __tablename__ = "mining_rewards"
    """Mining Rewards"""

    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE"), primary_key=True)
    address = Column(String)

    def __repr__(self):
        return "MiningReward(%s, %s)" % (self.txid, self.address)
