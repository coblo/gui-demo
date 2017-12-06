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

    address_from = Column(String, primary_key=True)
    address_to = Column(String, primary_key=True)
    perm_type = Column(Enum(PermTypes), primary_key=True)
    start_block = Column(Integer, primary_key=True)
    end_block = Column(Integer, primary_key=True)

    def __repr__(self):
        return "Vote(%s, %s, %s, %s)" % (self.txid, self.from_address, self.to_address, self.perm_type)

    @staticmethod
    def num_revokes(address, perm_type):
        return data_db().query(PendingVote).filter(
            PendingVote.address_to == address and PendingVote.perm_type == perm_type
            and PendingVote.start_block == 0 and PendingVote.end_block == 0).count()

    @staticmethod
    def num_grants(address, perm_type):
        from app.models import Permission
        return data_db().query(PendingVote).filter(
            PendingVote.address_to == address
            and PendingVote.perm_type == perm_type
            and PendingVote.start_block == 0
            and PendingVote.end_block == Permission.MAX_END_BLOCK
        ).count()

    @staticmethod
    def num_candidates():
        from app.models import Permission
        return data_db().query(PendingVote) \
            .filter((PendingVote.start_block == 0) & (PendingVote.end_block == Permission.MAX_END_BLOCK)) \
            .group_by(PendingVote.address_to).count()

    @staticmethod
    def get_candidates():
        from app.models import Permission
        return data_db().query(PendingVote) \
            .filter((PendingVote.start_block == 0) & (PendingVote.end_block == Permission.MAX_END_BLOCK)).all()

    @staticmethod
    def already_granted():
        from app.models import Permission, Profile
        return data_db().query(PendingVote.address_to, PendingVote.perm_type).filter(
            (PendingVote.address_from == Profile.get_active().address) & (PendingVote.start_block == 0) &
            (PendingVote.end_block == Permission.MAX_END_BLOCK)).all()

    @staticmethod
    def already_revoked():
        from app.models import Profile
        return data_db().query(PendingVote.address_to, PendingVote.perm_type).filter(
            (PendingVote.address_from == Profile.get_active().address) & (PendingVote.start_block == 0) &
            (PendingVote.end_block == 0)).all()
