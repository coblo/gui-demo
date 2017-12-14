# -*- coding: utf-8 -*-
"""Data model orm package"""
import logging
import peewee
import app
from app.models.address import Address
from app.models.block import Block
from app.models.currentvote import CurrentVote
from app.models.permission import Permission
from app.models.transaction import Transaction
from app.models.profile import Profile
from app.models.vote import Vote
from app.models.db import data_db, profile_db

log = logging.getLogger(__name__)


def init_profile_db():
    fp = app.PROFILE_DB_FILEPATH
    log.debug('init profile db at {}'.format(fp))
    profile_db.initialize(peewee.SqliteDatabase(fp))
    profile_db.connect()

    log.debug('check profile-db schema')

    if not check_table_ddl_against_model(profile_db, Profile):
        log.debug('profile-db schema outdated, resetting')
        profile_db.drop_tables([Profile], safe=True)
    else:
        log.debug("profile-db schema up to date")

    profile_db.create_tables([Profile], safe=True)

    return profile_db


def init_data_db():
    profile_obj = Profile.get_active()
    if profile_obj is None:
        raise RuntimeError('cannot init data db without active profile')
    fp = profile_obj.data_db_filepath
    log.debug('init data db at: {}'.format(fp))
    data_db.initialize(peewee.SqliteDatabase(fp))
    data_db.connect()
    log.debug("check data-db schema")
    models = [Address, CurrentVote, Block, Permission, Transaction, Vote]
    for model in models:
        log.debug("check {}-db schema".format(model.__name__.lower()))
        if not check_table_ddl_against_model(data_db, model):
            log.debug("{}-db schema outdated, resetting".format(model.__name__.lower()))
            data_db.drop_tables([model], safe=True)
        else:
            log.debug("{}-db schema up to date".format(model))

    data_db.create_tables(
        [Address, CurrentVote, Block, Permission, Transaction, Vote],
        safe=True
    )
    return data_db

def check_table_ddl_against_model(database, model) -> bool:
    # TODO make this dependent on driver. Peewee itself loses options when reading the schema from db
    db_table_ddl = database.execute_sql("select sql from sqlite_master where type = 'table' and name = '{}'".format(model.__name__.lower())).fetchone()
    model_table_ddl = database.compiler().create_table(model)
    if db_table_ddl:
        return db_table_ddl[0] == model_table_ddl[0]
    return False


if __name__ == '__main__':
    import app.helpers
    app.helpers.init_logging()
    init_profile_db()
    init_data_db()
    for t in Transaction.select():
        print(t)
