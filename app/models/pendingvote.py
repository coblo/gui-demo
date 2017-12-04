# -*- coding: utf-8 -*-
import logging

from sqlalchemy import String, Column, Enum, Integer, func, distinct

from app.enums import PermTypes
from app.models.db import data_base

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
    def num_revokes(data_db, perm_type):
        return (
            data_db.
            query(PendingVote.address_to, func.count("*").label("count")).
            filter(PendingVote.perm_type == perm_type and PendingVote.start_block == 0 and PendingVote.end_block == 0).
            group_by(PendingVote.address_to)
        ).all()

    @staticmethod
    def num_candidates(data_db):
        from app.models import Permission
        return (
            data_db.query(func.count(distinct(PendingVote.address_to))).
            filter((PendingVote.start_block == 0) & (PendingVote.end_block == Permission.MAX_END_BLOCK))
        ).scalar()

    @staticmethod
    def get_candidates(data_db):
        from app.models import Permission
        return (
            data_db.
            query(PendingVote.address_to, PendingVote.perm_type, func.count("*").label("grants")).
            filter((PendingVote.start_block == 0) & (PendingVote.end_block == Permission.MAX_END_BLOCK)).
            group_by(PendingVote.address_to, PendingVote.perm_type)
        ).all()

    @staticmethod
    def already_granted(data_db):
        from app.models import Permission, Profile
        from app.models.db import profile_session_scope
        with profile_session_scope() as session:
            profile = Profile.get_active(session)
        return data_db.query(PendingVote.address_to, PendingVote.perm_type).filter(
            (PendingVote.address_from == profile.address) & (PendingVote.start_block == 0) &
            (PendingVote.end_block == Permission.MAX_END_BLOCK)).all()

    @staticmethod
    def already_revoked(data_db):
        from app.models import Profile
        from app.models.db import profile_session_scope
        with profile_session_scope() as session:
            profile = Profile.get_active(session)
        return data_db.query(PendingVote.address_to, PendingVote.perm_type).filter(
            (PendingVote.address_from == profile.address) & (PendingVote.start_block == 0) &
            (PendingVote.end_block == 0)).all()
