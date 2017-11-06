# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db

from .address import Address
from .permission import Permission


log = logging.getLogger(__name__)


class VotingRound(peewee.Model):
    """Permission votings"""

    GRANT, REVOKE, SCOPED_GRANT = 0, 1, 2
    VOTE_TYPES = (
        (GRANT, 'Grant'),
        (REVOKE, 'Revoke'),
        (SCOPED_GRANT, 'Scoped Grant'),
    )

    MAX_END_BLOCK = 4294967295

    first_vote = peewee.DateTimeField()
    address = peewee.ForeignKeyField(Address, related_name='votings')
    perm_type = peewee.CharField(choices=Permission.PERM_TYPES)
    start_block = peewee.IntegerField()
    end_block = peewee.IntegerField()
    approbations = peewee.IntegerField()
    vote_type = peewee.SmallIntegerField(choices=VOTE_TYPES, null=True)

    class Meta:
        database = data_db
        primary_key = peewee.CompositeKey('address', 'perm_type', 'start_block', 'end_block')

    def set_vote_type(self):
        if self.start_block == self.end_block == 0:
            self.vote_type = self.REVOKE
        elif self.end_block == 0 and self.end_block == self.MAX_END_BLOCK:
            self.vote_type = self.GRANT
        else:
            self.vote_type = self.SCOPED_GRANT

    @staticmethod
    def num_candidates():
        return VotingRound.select().where(
            VotingRound.start_block == 0,
            VotingRound.end_block == VotingRound.MAX_END_BLOCK
        ).count()
