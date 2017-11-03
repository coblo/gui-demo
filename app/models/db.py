# -*- coding: utf-8 -*-
"""Database objects.

The application needs to setup some path and select configurtion dependent databases.
For example initialization of data_db depends on existing profile db and active
profile object. So we use a proxies to deffer init to a later runtime state.
See models.__init__.py for initialization functions.
"""
import peewee


profile_db = peewee.Proxy()
data_db = peewee.Proxy()
