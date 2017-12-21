# -*- coding: utf-8 -*-
import logging

from sqlalchemy import Column, String, ForeignKey, Integer, and_, or_
from sqlalchemy import exists

from app.models.db import data_base

log = logging.getLogger(__name__)


class ISCC(data_base):
    __tablename__ = "isccs"

    iscc_id = Column(Integer, autoincrement=True, primary_key=True)
    txid = Column(String, ForeignKey('transactions.txid', ondelete="CASCADE", deferrable=True, initially="DEFERRED"))
    meta_id = Column(String, index=True)
    content_id = Column(String, index=True)
    data_id = Column(String, index=True)
    instance_id = Column(String, index=True)
    address = Column(String)
    title = Column(String)

    def __repr__(self):
        return "(%s-%s-%s-%s)" % (self.meta_id, self.content_id, self.data_id, self.instance_id)

    @staticmethod
    def get_conflicts(data_db, meta_id, content_id, data_id, instance_id) -> bool:
        return data_db.query(ISCC).filter(or_(meta_id == ISCC.meta_id, content_id == ISCC.content_id,
                                              data_id == ISCC.data_id, instance_id == ISCC.instance_id)).all()

    @staticmethod
    def already_exists(data_db, meta_id, content_id, data_id, instance_id) -> bool:
        return data_db.query(exists().where(and_(meta_id == ISCC.meta_id, content_id == ISCC.content_id,
                                                 data_id == ISCC.data_id, instance_id == ISCC.instance_id))).scalar()

    @staticmethod
    def get_all_iscc(data_db) -> []:
        from app.models import Transaction, Block
        return data_db.query(ISCC, Block.time).join(Transaction, Block).order_by(Block.time.desc()).all()

    @staticmethod
    def filter_iscc(data_db, search_term) -> []:
        from app.models import Transaction, Block
        return data_db.query(ISCC, Block.time).join(Transaction, Block)\
            .filter(or_(
                ISCC.title.ilike("%" + search_term + "%"),
                ISCC.address.ilike("%" + search_term + "%"),
                ISCC.meta_id.ilike("%" + search_term + "%"),
                ISCC.content_id.ilike("%" + search_term + "%"),
                ISCC.data_id.ilike("%" + search_term + "%"),
                ISCC.instance_id.ilike("%" + search_term + "%")
            )).order_by(Block.time.desc()).all()
