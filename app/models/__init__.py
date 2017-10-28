# -*- coding: utf-8 -*-
"""Data model orm package"""
import logging
import peewee
import app
from app.models.transaction import Transaction
from app.models.profile import Profile
from app.models.db import data_db, profile_db

log = logging.getLogger(__name__)


def init_profile_db():
    fp = app.PROFILE_DB_FILEPATH
    log.debug('init profile db at {}'.format(fp))
    profile_db.initialize(peewee.SqliteDatabase(fp))
    profile_db.connect()
    profile_db.create_tables([Profile], safe=True)
    if not Profile.get_active():
        log.debug('no default profile... creating one.')
        with profile_db.atomic():
            Profile.create_default_profile()
    return profile_db


def init_data_db():
    profile_obj = Profile.get_active()
    if profile_obj is None:
        raise RuntimeError('cannot init data db without active profile')
    fp = profile_obj.data_db_filepath
    log.debug('init data db at: {}'.format(fp))
    data_db.initialize(peewee.SqliteDatabase(fp))
    data_db.connect()
    data_db.create_tables([Transaction], safe=True)
    return data_db


if __name__ == '__main__':
    import app.helpers
    app.helpers.init_logging()
    init_profile_db()
    init_data_db()
    for t in Transaction.select():
        print(t)
