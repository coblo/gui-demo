# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Enum

from app.models.db import data_base
from app.enums import PermTypes

log = logging.getLogger(__name__)


class Vote(data_base):
    __tablename__ = "votes"

    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE"), primary_key=True)
    from_address = Column(String, ForeignKey("addresses.address")) # todo: wollen wir das? eigentlich unnötig wir brauchen diese Verknüpfung nicht
    to_address = Column(String, ForeignKey("addresses.address")) # todo: ebenso
    perm_type = Column(Enum(PermTypes), primary_key=True)


    def __repr__(self):
        return "Vote(%s, %s, %s, %s)" % (self.txid, self.from_address, self.to_address, self.perm_type)
