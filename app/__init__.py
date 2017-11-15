# -*- coding: utf-8 -*-
"""Global constants and pre-app initialization stuff."""
from os.path import abspath, dirname, join
import sys
import appdirs


ORG_NAME = 'Content-Blockchain'
ORG_DOMAIN = 'content-blockchain.org'
APP_NAME = 'Charm'
MAJOR = 0
MINOR = 1
PATCH = 0
APP_VERSION = '{}.{}.{}'.format(MAJOR, MINOR, PATCH)


if getattr(sys, "frozen", False):
    APP_DIR = dirname(sys.executable)
else:
    APP_DIR = dirname(dirname(abspath(__file__)))

DATA_DIR = appdirs.user_data_dir(APP_NAME, ORG_NAME)
PROFILE_DB_FILENAME = 'profile.db'
PROFILE_DB_FILEPATH = join(DATA_DIR, PROFILE_DB_FILENAME)
DEFAULT_PROFILE_NAME = 'default'
DEFAULT_RPC_HOST = '127.0.0.1'
DEFAULT_RPC_PORT = 8374

ADMIN_CONSENUS_MINE = 0.17724500
ADMIN_CONSENUS_ADMIN = 0.51

NODE_BOOTSTRAP = 'charm@85.197.78.50:8375'

CURRENCY_CODE = 'CHM'


def init():
    import sys
    import traceback
    from app import helpers
    from app import models
    sys.excepthook = traceback.print_exception
    helpers.init_logging()
    helpers.init_data_dir()
    models.init_profile_db()
    models.init_data_db()
