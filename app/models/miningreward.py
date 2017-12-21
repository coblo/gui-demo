# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from sqlalchemy import Column, String, ForeignKey, func

from app.models.db import data_base

log = logging.getLogger(__name__)


class MiningReward(data_base):
    __tablename__ = "mining_rewards"
    """Mining Rewards"""

    block = Column(String, ForeignKey('blocks.hash', ondelete="CASCADE", deferrable=True, initially="DEFERRED"), primary_key=True)
    address = Column(String)

    def __repr__(self):
        return "MiningReward(%s, %s)" % (self.block, self.address)


    @staticmethod
    def last_mined(data_db):
        from app.models import Block
        return (
            data_db.
            query(func.max(Block.mining_time).label("last_mined"), MiningReward.address).
            join(MiningReward).
            group_by(MiningReward.address)
        ).all()

    @staticmethod
    def mined_last_24h(data_db):
        from app.models import Block
        return (
            data_db.
            query(MiningReward.address, func.count("*").label("count")).
            join(Block).filter(datetime.now() - timedelta(days=1) <= Block.mining_time)
            .group_by(MiningReward.address)
        ).all()
