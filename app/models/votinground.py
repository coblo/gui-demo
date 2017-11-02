# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db
from app.enums import VoteType, PermType

from .address import Address


log = logging.getLogger(__name__)


class VotingRound(peewee.Model):
    """Permission votings"""

    MAX_END_BLOCK = 4294967295

    first_vote = peewee.DateTimeField()
    address = peewee.ForeignKeyField(Address, related_name='votings')
    perm_type = peewee.CharField(choices=PermType)
    start_block = peewee.IntegerField()
    end_block = peewee.IntegerField()
    approbations = peewee.IntegerField()
    vote_type = peewee.CharField(choices=VoteType, null=True)

    class Meta:
        database = data_db
        primary_key = peewee.CompositeKey('address', 'perm_type', 'start_block', 'end_block')

    def set_vote_type(self):
        if self.start_block == self.end_block == 0:
            self.vote_type = VoteType.REVOKE.value
        if self.end_block == 0 and self.end_block == self.MAX_END_BLOCK:
            self.vote_type = VoteType.GRANT.value
        else:
            self.vote_type = VoteType.SCOPED_GRANT.value

    @staticmethod
    def num_candidates():
        return VotingRound.select().where(
            VotingRound.start_block == 0,
            VotingRound.end_block == VotingRound.MAX_END_BLOCK
        ).count()
