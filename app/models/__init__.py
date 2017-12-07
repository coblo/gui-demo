# -*- coding: utf-8 -*-
"""Data model orm package"""
import logging
import sqlalchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.sql.ddl import CreateTable

import app
from app.models.address import Address
from app.models.alias import Alias
from app.models.block import Block
from app.models.miningreward import MiningReward
from app.models.wallet_transaction import WalletTransaction
from app.models.pendingvote import PendingVote
from app.models.permission import Permission
from app.models.transaction import Transaction
from app.models.timestamp import Timestamp
from app.models.profile import Profile, Profile_Base
from app.models.vote import Vote
from app.models.db import data_db, profile_db, data_base

log = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_profile_db():
    fp = app.PROFILE_DB_FILEPATH
    log.debug('init profile db at {}'.format(fp))
    engine = sqlalchemy.create_engine('sqlite:///{}'.format(fp))
    # create the database
    Profile_Base.metadata.create_all(engine)

    profile_db.configure(bind=engine)

    log.debug("check {}-db schema".format(Profile.__table__.name))
    if not check_table_ddl_against_model(profile_db, Profile.__table__):
        log.debug("{}-db schema outdated, resetting".format(Profile.__table__.name))
        Profile.__table__.drop(engine)
    else:
        log.debug("{}-db schema up to date".format(Profile.__table__.name))

    return profile_db


def init_data_db():
    profile_obj = Profile.get_active()
    if profile_obj is None:
        raise RuntimeError('cannot init data db without active profile')
    fp = profile_obj.data_db_filepath

    log.debug('init data db at: {}'.format(fp))
    engine = sqlalchemy.create_engine('sqlite:///{}'.format(fp))
    data_db.configure(bind=engine)

    log.debug("check data-db schema")
    for table_name, table in data_base.metadata.tables.items():
        log.debug("check {}-db schema".format(table.name))
        if not check_table_ddl_against_model(data_db, table):
            log.debug("{}-db schema outdated, resetting".format(table.name))
            table.drop(engine)
        else:
            log.debug("{}-db schema up to date".format(table.name))

    data_base.metadata.create_all(engine)
    return data_db


def check_table_ddl_against_model(database, table) -> bool:
    if database.bind.name == "sqlite":
        db_table_ddl = database().execute("select sql from sqlite_master where type = 'table' and name = '{}'".format(table.name)).scalar()
    else:
        raise Exception("Unsupported database dialect:{}".format(database.bind.name))

    if db_table_ddl:
        return str.strip(CreateTable(table).compile(database.bind).string) == str.strip(db_table_ddl)
    return True


if __name__ == '__main__':
    import app.helpers
    app.helpers.init_logging()
    init_profile_db()
    init_data_db()
    for t in Transaction.select():
        print(t)
