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
from app.models.db import data_db, profile_db, data_base, profile_session_scope

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

    profile_db.configure(bind=engine)

    log.debug("check {}-db schema".format(Profile.__table__.name))
    backup_profiles = []
    if not check_table_ddl_against_model(profile_db, Profile.__table__):
        log.debug("{}-db schema outdated, resetting".format(Profile.__table__.name))
        if engine.dialect.has_table(engine, "profiles"):
            for profile in profile_db().execute('SELECT * FROM profiles').fetchall():
                backup_profiles.append(profile)

            Profile.__table__.drop(engine)
        elif engine.dialect.has_table(engine, "profile"):
            for profile in profile_db().execute('SELECT * FROM profile').fetchall():
                backup_profiles.append(profile)
    else:
        log.debug("{}-db schema up to date".format(Profile.__table__.name))

    # create the database
    Profile_Base.metadata.create_all(engine)

    with profile_session_scope() as session:
        for profile in backup_profiles:
            session.add(Profile(
                name=profile.name if 'name' in profile else '',
                rpc_host=profile.rpc_host if 'rpc_host' in profile else '127.0.0.1',
                rpc_port=profile.rpc_port if 'rpc_port' in profile else '8374',
                rpc_user=profile.rpc_user if 'rpc_user' in profile else 'multichainrpc',
                rpc_password=profile.rpc_password if 'rpc_password' in profile else '',
                rpc_use_ssl=profile.rpc_use_ssl if 'rpc_use_ssl' in profile else 0,
                manage_node=profile.manage_node if 'manage_node' in profile else 1,
                exit_on_close=profile.exit_on_close if 'exit_on_close' in profile else 1,
                active=profile.active if 'active' in profile else 0,
                alias=profile.alias if 'alias' in profile else '',
                address=profile.address if 'address' in profile else '',
                balance=profile.balance if 'balance' in profile else 0,
                is_admin=profile.is_admin if 'is_admin' in profile else 0,
                is_miner=profile.is_miner if 'is_miner' in profile else 0,
            ))

    return profile_db


def init_data_db():
    fp = ''
    with profile_session_scope() as session:
        profile_obj = Profile.get_active(session)
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

    return str.strip(CreateTable(table).compile(database.bind).string) == str.strip(db_table_ddl or '')


if __name__ == '__main__':
    import app.helpers
    app.helpers.init_logging()
    init_profile_db()
    init_data_db()
    for t in Transaction.select():
        print(t)
