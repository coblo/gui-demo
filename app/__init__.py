# -*- coding: utf-8 -*-
"""Global constants and pre-app initialization stuff."""
from os import environ
from os.path import abspath, dirname, join
import sys
import appdirs

# Enable QT High-Dpi Support
environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = "1"

ORG_NAME = 'Content-Blockchain'
ORG_DOMAIN = 'content-blockchain.org'
APP_NAME = 'Coblo'
MAJOR = 1
MINOR = 0
PATCH = 1
APP_VERSION = '{}.{}.{}'.format(MAJOR, MINOR, PATCH)


def is_frozen():
    """Determine if application is running as frozen binary"""
    return getattr(sys, 'frozen', False)


if is_frozen():
    APP_DIR = join(dirname(sys.executable), 'lib')
else:
    APP_DIR = dirname(dirname(abspath(__file__)))

DATA_DIR = appdirs.user_data_dir(APP_NAME, ORG_NAME, APP_VERSION)
PROFILE_DB_FILENAME = 'profile_{}.db'.format(APP_VERSION)
PROFILE_DB_FILEPATH = join(DATA_DIR, PROFILE_DB_FILENAME)
DEFAULT_PROFILE_NAME = 'default'
DEFAULT_RPC_HOST = '127.0.0.1'
DEFAULT_RPC_PORT = 9719

ADMIN_CONSENUS_MINE = 0.17724500
ADMIN_CONSENUS_ADMIN = 0.51

NODE_BOOTSTRAP = 'coblo2@85.197.78.51:9719'

CURRENCY_CODE = 'CBL'

# From current chain params.dat needed for address generation.
TESTNET_ADDRESS_PUBKEYHASH_VERSION = '0046e454'
TESTNET_ADDRESS_SCRIPTHASH_VERSION = '054b9e59'
TESTNET_ADDRESS_CHECKSUM_VALUE = 'd8a558e6'
TESTNET_PRIVATE_KEY_VERSION = '807c3b9f'

TESTNET2_ADDRESS_PUBKEYHASH_VERSION = 'ca'
TESTNET2_ADDRESS_SCRIPTHASH_VERSION = 'cb'
TESTNET2_ADDRESS_CHECKSUM_VALUE = '00000000'
TESTNET2_PRIVATE_KEY_VERSION = 'cc'

GET_COINS_URL = 'https://t.me/ContentBlockchainBeta'

STREAM_ALIAS = 'alias'
STREAM_ISCC = 'iscc'
STREAM_TIMESTAMP = 'timestamp'


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


def is_first_start(profile_db):
    from app.models.profile import Profile
    """Check if the applications needs to be configured"""
    if not Profile.get_active(profile_db):
        return True
    else:
        return False
