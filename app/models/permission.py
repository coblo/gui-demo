# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum, Integer, PrimaryKeyConstraint

from app import enums
from app.models.db import data_db, data_base
from app.enums import PermTypes

log = logging.getLogger(__name__)


class Permission(data_base):

    __tablename__ = "permissions"
    """Address permissions"""

    MAX_END_BLOCK = 4294967295

    address = Column(String, ForeignKey("addresses.address"), primary_key=True)
    perm_type = Column(Enum(PermTypes), primary_key=True)
    start_block = Column(Integer)
    end_block = Column(Integer)


    def __repr__(self):
        return "Permission(%s, %s, %s, %s)" % (
            self.address_id[:4], self.perm_type, self.start_block, self.end_block
        )

    #todo: alles ab hier ungetestet
    @staticmethod
    def validators(): # todo: eigentlcih so falsch, man muss gucken wer für den AKTUELLEN Block die Rechte hat
        return data_db().query(Permission).filter(
            Permission.perm_type == enums.MINE,
            Permission.start_block == 0,
            Permission.end_block == Permission.MAX_END_BLOCK
        ).all()

    @staticmethod
    def guardians():
        return data_db().query(Permission).filter(
            Permission.perm_type == enums.ADMIN,
            Permission.start_block == 0,
            Permission.end_block == Permission.MAX_END_BLOCK
        ).all()

    @staticmethod
    def num_validators():
        return Permission.validators().count()

    @staticmethod
    def num_guardians():
        return Permission.guardians().count()

