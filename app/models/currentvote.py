# -*- coding: utf-8 -*-
import logging
import peewee
from app.models.db import data_db

from .address import Address
from .permission import Permission


log = logging.getLogger(__name__)


class CurrentVote(peewee.Model):
    """Current permission votings"""

    GRANT, REVOKE, SCOPED_GRANT = 0, 1, 2
    VOTE_TYPES = (
        (GRANT, 'Grant'),
        (REVOKE, 'Revoke'),
        (SCOPED_GRANT, 'Scoped Grant'),
    )

    MAX_END_BLOCK = 4294967295

    address = peewee.ForeignKeyField(Address, related_name='current_votings')
    perm_type = peewee.CharField(choices=Permission.PERM_TYPES)
    start_block = peewee.IntegerField()
    end_block = peewee.IntegerField()
    given_from = peewee.ForeignKeyField(Address, related_name='current_votes_given')
    vote_type = peewee.SmallIntegerField(choices=VOTE_TYPES, null=True)

    class Meta:
        database = data_db
        primary_key = peewee.CompositeKey('address', 'perm_type', 'start_block', 'end_block', 'given_from')

    def set_vote_type(self):
        if self.start_block == self.end_block == 0:
            self.vote_type = self.REVOKE
        elif self.end_block == 0 and self.end_block == self.MAX_END_BLOCK:
            self.vote_type = self.GRANT
        else:
            self.vote_type = self.SCOPED_GRANT
        self.save()

    @staticmethod
    def num_candidates():
        return CurrentVote.select().where(
            CurrentVote.start_block == 0,
            CurrentVote.end_block == CurrentVote.MAX_END_BLOCK
        ).group_by(
            CurrentVote.address
        ).count()

    @staticmethod
    def get_candidates():
        return CurrentVote.select().where(
            CurrentVote.start_block == 0,
            CurrentVote.end_block == CurrentVote.MAX_END_BLOCK
        ).group_by(
            CurrentVote.address
        )
