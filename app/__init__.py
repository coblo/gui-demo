# -*- coding: utf-8 -*-
"""Global constants and pre-app initialization stuff."""
from os.path import abspath, dirname, join, exists
from os import environ
import sys
import appdirs

# Enable QT High-Dpi Support
environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = "1"

ORG_NAME = 'Content-Blockchain'
ORG_DOMAIN = 'content-blockchain.org'
APP_NAME = 'Coblo'
MAJOR = 0
MINOR = 2
PATCH = 2
APP_VERSION = '{}.{}.{}'.format(MAJOR, MINOR, PATCH)


def is_frozen():
    """Determine if application is running as frozen binary"""
    return getattr(sys, 'frozen', False)


if is_frozen():
    APP_DIR = join(dirname(sys.executable), 'lib')
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

NODE_BOOTSTRAP = 'coblo@85.197.78.50:8375'

CURRENCY_CODE = 'CHM'

# From current chain params.dat needed for address generation.
TESTNET_ADDRESS_PUBKEYHASH_VERSION = '0046e454'
TESTNET_ADDRESS_SCRIPTHASH_VERSION = '054b9e59'
TESTNET_ADDRESS_CHECKSUM_VALUE = 'd8a558e6'
TESTNET_PRIVATE_KEY_VERSION = '807c3b9f'

GET_COINS_URL = 'https://t.me/ContentBlockchainBeta'


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


def is_first_start():
    """Check if the applications needs to be configured"""
    if not exists(PROFILE_DB_FILEPATH):
        return True
    else:
        return False
