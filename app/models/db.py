# -*- coding: utf-8 -*-
"""Database objects.

The application needs to setup some path and select configuration dependent databases.
For example initialization of data_db depends on existing profile db and active
profile object. So we use a proxies to deffer init to a later runtime state.
See models.__init__.py for initialization functions.
"""
from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

profile_db = scoped_session(sessionmaker(expire_on_commit=False))
# todo rename those e.g. cache_db
data_db = scoped_session(sessionmaker(expire_on_commit=False))
data_base = declarative_base()


@contextmanager
def profile_session_scope():
    """Provide a transactional scope around a series of operations."""
    session = profile_db()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.expunge_all()
        session.close()


@contextmanager
def data_session_scope():
    """Provide a transactional scope around a series of operations."""
    session = data_db()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.expunge_all()
        session.close()
