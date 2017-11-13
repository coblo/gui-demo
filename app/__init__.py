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

NODE_BOOTSTRAP = 'charm@85.197.78.50:8375'

CURRENCY_CODE = 'CHM'

# From current chain params.dat needed for address generation.
TESTNET_ADDRESS_PUBKEYHASH_VERSION = '0046e454'
TESTNET_ADDRESS_SCRIPTHASH_VERSION = '054b9e59'
TESTNET_ADDRESS_CHECKSUM_VALUE = 'd8a558e6'
TESTNET_PRIVATE_KEY_VERSION = '807c3b9f'


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
