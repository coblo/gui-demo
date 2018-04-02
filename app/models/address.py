# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, exists
from sqlalchemy.event import listens_for

from app.models.db import data_base
from app.signals import signals


class Address(data_base):
    __tablename__ = 'addresses'

    """
    Only a list of all addresses that appeared in the chain.
    """

    address = Column(String, primary_key=True)

    def __repr__(self):
        return 'Address(%s)' % (self.address)

    @staticmethod
    def create_if_not_exists(data_db, address):
        if not data_db.query(exists().where(Address.address == address)).scalar():
            data_db.add(Address(address=address))


@listens_for(Address, "after_insert")
def after_update(mapper, connection, address):
    signals.new_address.emit()