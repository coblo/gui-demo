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


def init_data_dir():
    if not os.path.exists(app.DATA_DIR):
        log.debug('creating data dir {}'.format(app.DATA_DIR))
        os.makedirs(app.DATA_DIR, exist_ok=True)
    return app.DATA_DIR


def init_node_data_dir():
    from app.models import Profile
    from app.models.db import profile_session_scope
    with profile_session_scope() as session:
        profile = Profile.get_active(session)
        ndd = os.path.join(app.DATA_DIR, 'node_' + profile.name)
        if profile.manage_node:
            if not os.path.exists(ndd):
                log.debug('create node data dir {}'.format(ndd))
                os.makedirs(ndd, exist_ok=True)
        return ndd


def gen_password(length=36):
    chars = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


def batchwise(rng, chunksize):
    """Batchwise api iteration.

    >>>batchwise(range(1501, 1750), 100)
    ['1501-1600', '1601-1700', '1701-1750']
    """
    for i in range(0, len(rng)+1, chunksize):
        batch = rng[i:i+chunksize - 1]
        yield '{}-{}'.format(batch.start, batch.stop)
