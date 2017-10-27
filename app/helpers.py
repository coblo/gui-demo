# -*- coding: utf-8 -*-
"""Assorted helper functions"""
import os
import sys
import random
import string
import logging
import app

log = logging.getLogger(__name__)


def init_logging():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)


def init_data_dir():
    if not os.path.exists(app.DATA_DIR):
        log.debug('creating data dir {}'.format(app.DATA_DIR))
        os.makedirs(app.DATA_DIR, exist_ok=True)
    return app.DATA_DIR


def init_profile_db():
    log.debug('init profile database')
    from app.models import profile_db, Profile
    profile_db.connect()
    profile_db.create_tables([Profile], safe=True)
    if not Profile.get_active():
        log.debug('create default profile')
        with profile_db.atomic():
            profile = Profile.create_default_profile()
    return profile_db


def init_node_data_dir():
    from app.models import Profile
    profile = Profile.get_active()
    ndd = os.path.join(app.DATA_DIR, 'node_' + profile.name)
    if profile.manage_node:
        if not os.path.exists(ndd):
            log.debug('create node data dir {}'.format(ndd))
            os.makedirs(ndd, exist_ok=True)
    return ndd


def gen_password(length=36):
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


