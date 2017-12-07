# -*- coding: utf-8 -*-
from sqlalchemy import Column, String
from sqlalchemy import exists

from app.models.db import data_db, data_base


class Address(data_base):
    __tablename__ = 'addresses'

    """
    Only a list of all addresses that appeared in the chain.
    """

    address = Column(String, primary_key=True)

    class Meta:
        database = data_db

    def __repr__(self):
        return 'Address(%s)' % (self.address)

    @staticmethod
    def create_if_not_exists(address):
        if not data_db().query(exists().where(Address.address == address)).scalar():
            data_db().add(Address(address=address))

    # @classmethod #todo: in die Klassen mining_reqards und votes verlagern
    # def with_last_mined(cls):
    #     """Queryset annotated with .last_mined"""
    #     from app.models import Block
    #     return cls.select().annotate(Block, fn.MAX(Block.time).alias('last_mined'))
    #
    # @classmethod
    # def with_last_voted(cls):
    #     """Queryset annotated with .last_voted"""
    #     from app.models import Vote
    #     return cls.select().annotate(Vote, fn.MAX(Vote.time).alias('last_voted'))
    #
    # def get_last_mined(self):
    #     from app.models import Block
    #     latest_block = self.mined_blocks.order_by(Block.time.desc()).first()
    #     if latest_block:
    #         return latest_block.time
    #
    # def get_last_voted(self):
    #     from app.models import Vote
    #     latest_vote = self.votes_given.order_by(Vote.time.desc()).first()
    #     if latest_vote:
    #         return latest_vote.time
