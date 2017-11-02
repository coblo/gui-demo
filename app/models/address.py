# -*- coding: utf-8 -*-
import logging
import peewee

from app.models.db import data_db
from app.enums import PermType


log = logging.getLogger(__name__)


class Address(peewee.Model):
    """
    TODO: use query annotations or denormalize fields
    """

    address = peewee.CharField(primary_key=True)
    alias = peewee.CharField(unique=True, null=True)

    class Meta:
        database = data_db

    def __repr__(self):
        return 'Address(%s, %s)' % (self.address, self.alias)

    def last_mined(self):
        from app.models import Block
        latest_block = self.mined_blocks.order_by(Block.time.desc()).first()
        if latest_block:
            return latest_block.time

    def last_voted(self):
        return 'TODO find out :)'

    def num_validator_revokes(self):
        from app.models import VotingRound
        return VotingRound.select().where(
            (VotingRound.address == self) &
            (VotingRound.perm_type == PermType.MINE) &
            (VotingRound.start_block == 0) &
            (VotingRound.end_block == 0)
        ).count()

    def num_guardian_revokes(self):
        from app.models import VotingRound
        return VotingRound.select().where(
            (VotingRound.address == self) &
            (VotingRound.perm_type == PermType.ADMIN) &
            (VotingRound.start_block == 0) &
            (VotingRound.end_block == 0)
        ).count()
