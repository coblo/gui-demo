# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, Enum, Integer

from app import enums
from app.enums import PermTypes
from app.models.db import data_base

log = logging.getLogger(__name__)


class Permission(data_base):

    __tablename__ = "permissions"
    """Address permissions"""

    MAX_END_BLOCK = 4294967295

    address = Column(String, primary_key=True)
    perm_type = Column(Enum(PermTypes), primary_key=True)
    start_block = Column(Integer)
    end_block = Column(Integer)


    def __repr__(self):
        return "Permission(%s, %s, %s, %s)" % (
            self.address_id[:4], self.perm_type, self.start_block, self.end_block
        )

    #todo: alles ab hier ungetestet
    @staticmethod
    def validators(data_db): # todo: eigentlcih so falsch, man muss gucken wer für den AKTUELLEN Block die Rechte hat
        return data_db.query(Permission).filter(
            (Permission.perm_type == enums.MINE) &
            (Permission.start_block == 0) &
            (Permission.end_block == Permission.MAX_END_BLOCK)
        ).all()

    @staticmethod
    def guardians(data_db):
        return data_db.query(Permission).filter(
            (Permission.perm_type == enums.ADMIN) &
            (Permission.start_block == 0) &
            (Permission.end_block == Permission.MAX_END_BLOCK)
        ).all()

    @staticmethod
    def num_validators(data_db):
        return data_db.query(Permission).filter(
            (Permission.perm_type == enums.MINE) &
            (Permission.start_block == 0) &
            (Permission.end_block == Permission.MAX_END_BLOCK)
        ).count()

    @staticmethod
    def num_guardians(data_db):
        return data_db.query(Permission).filter(
            (Permission.perm_type == enums.ADMIN) &
            (Permission.start_block == 0) &
            (Permission.end_block == Permission.MAX_END_BLOCK)
        ).count()

    @staticmethod
    def get_permissions_for_address(data_db, address) -> (bool, bool):
        from sqlalchemy import exists
        result = data_db.query(
            exists().where(
                (Permission.address == address) &
                (Permission.perm_type == enums.ADMIN) &
                (Permission.start_block == 0) &
                (Permission.end_block == Permission.MAX_END_BLOCK)
            ).label("is_admin"),
            exists().where(
                (Permission.address == address) &
                (Permission.perm_type == enums.MINE) &
                (Permission.start_block == 0) &
                (Permission.end_block == Permission.MAX_END_BLOCK)
            ).label("is_miner"),
        ).first()
        return result
