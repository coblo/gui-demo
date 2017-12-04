# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Integer, exists
from sqlalchemy.event import listens_for
from sqlalchemy.orm import aliased

from app.models.db import data_base, profile_session_scope

log = logging.getLogger(__name__)


class Alias(data_base):
    __tablename__ = "alias"
    """Alias Changes"""

    alias_id = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    address = Column(String)
    alias = Column(String)

    def __repr__(self):
        return "Alias(%s, %s, %s)" % (self.txid, self.address, self.alias)

    @staticmethod
    def get_aliases(data_db):
        from app.models import Block, Transaction
        alias_list = {}
        for alias_entry in data_db.query(Alias, Block).join(Transaction, Block).order_by(Block.time.desc()).all():
            if alias_entry.Alias.address in alias_list.keys() or alias_entry.Alias.alias in alias_list.values():
                continue
            alias_list[alias_entry.Alias.address] = alias_entry.Alias.alias
        return alias_list

    @staticmethod
    def get_alias_by_address(data_db, address):
        alias_list = Alias.get_aliases(data_db)
        if address in alias_list:
            return alias_list[address]
        else:
            return ''

    @staticmethod
    def alias_in_use(data_db, alias):
        aliased_class = aliased(Alias)
        stmt = ~data_db.query().filter((aliased_class.address == Alias.address) & (aliased_class.alias_id > Alias.alias_id)).exists()
        return data_db.query(exists().where(Alias.alias == alias).where(stmt)).scalar()


@listens_for(Alias, "after_insert")
def after_update(mapper, connection, alias):
    from app.models import Profile
    with profile_session_scope() as session:
        profile = Profile.get_active(session)
        if alias.address == profile.address:
            profile.alias = alias.alias
