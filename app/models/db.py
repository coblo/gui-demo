# -*- coding: utf-8 -*-
"""Database objects.

The application needs to setup some path and select configuration dependent databases.
For example initialization of data_db depends on existing profile db and active
profile object. So we use a proxies to deffer init to a later runtime state.
See models.__init__.py for initialization functions.
"""
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

profile_db = scoped_session(sessionmaker())
# todo rename those e.g. cache_db
data_db = scoped_session(sessionmaker())
data_base = declarative_base()
