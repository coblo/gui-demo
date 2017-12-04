# -*- coding: utf-8 -*-
import logging
from sqlalchemy import String, Column, ForeignKey, Enum, Integer, PrimaryKeyConstraint

from app.models.db import data_db, data_base
from app.enums import PermTypes

log = logging.getLogger(__name__)


class PendingVote(data_base):

    __tablename__ = "pending_votes"
    """Pending permission votings"""

    MAX_END_BLOCK = 4294967295

    address_from = Column(String, ForeignKey("addresses.address"), primary_key=True) # todo: unnötig? siehe votes
    address_to = Column(String, ForeignKey("addresses.address"), primary_key=True)
    perm_type = Column(Enum(PermTypes), primary_key=True)
    start_block = Column(Integer, primary_key=True)
    end_block = Column(Integer, primary_key=True)

    class Meta:
        database = data_db

    def set_vote_type(self): #todo:
        # if self.start_block == self.end_block == 0:
        #     self.vote_type = self.REVOKE
        # elif self.end_block == 0 and self.end_block == self.MAX_END_BLOCK:
        #     self.vote_type = self.GRANT
        # else:
        #     self.vote_type = self.SCOPED_GRANT
        # self.save()
        pass

    @staticmethod
    def num_candidates(): #todo:
        # return PendingVote.select().where(
        #     PendingVote.start_block == 0,
        #     PendingVote.end_block == PendingVote.MAX_END_BLOCK
        # ).group_by(
        #     PendingVote.address
        # ).count()
        pass

    @staticmethod
    def get_candidates(): #todo:
        # return PendingVote.select().where(
        #     PendingVote.start_block == 0,
        #     PendingVote.end_block == PendingVote.MAX_END_BLOCK
        # ).group_by(
        #     PendingVote.address
        # )
        pass
