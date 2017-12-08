# -*- coding: utf-8 -*-
import getpass
import logging
import os
from decimal import Decimal

from sqlalchemy import String, Column, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

import app
from app.helpers import gen_password
from app.models.db import profile_db
from app.signals import signals

log = logging.getLogger(__name__)
Profile_Base = declarative_base()


class Profile(Profile_Base):
    """Application profile to mangage different Nodes/Accounts"""
    __tablename__ = 'profiles'

    name = Column(String, primary_key=True)
    rpc_host = Column(String)
    rpc_port = Column(String)
    rpc_user = Column(String)
    rpc_password = Column(String)
    rpc_use_ssl = Column(Boolean)
    manage_node = Column(Boolean)
    exit_on_close = Column(Boolean)
    active = Column(Boolean)

    # state of variables shown in gui
    alias = Column(String, default='')
    address = Column(String, default='')
    balance = Column(Float(asdecimal=True), default=Decimal())
    is_admin = Column(Boolean, default=False)
    is_miner = Column(Boolean, default=False)

    def __repr__(self):
        return 'Profile(%s, %s, %s...)' % (self.name, self.rpc_host, self.rpc_user)

    def save(self, *args, **kwargs): # todo: ungetestet
        signals.profile_changed.emit(self)

    def set_active(self):
        profile_db().add(self) # todo: Muss man nicht bei allen anderen active auf false setzen?
        self.active = True
        profile_db().commit()

    @property
    def data_db_filepath(self):
        """Return database path for this profile"""
        return os.path.join(app.DATA_DIR, self.name + '-data.db')

    @staticmethod
    def get_active() -> 'Profile':
        """Return currently active Pofile"""
        return profile_db.query(Profile).filter(Profile.active == True).first()

    @staticmethod
    def create_default_profile(): # todo: ungetestet
        """Create a default profile for local node connection"""
        log.debug('creating default profile')
        default_profile = Profile(
            name=app.DEFAULT_PROFILE_NAME,
            rpc_host=app.DEFAULT_RPC_HOST,
            rpc_port=app.DEFAULT_RPC_PORT,
            rpc_user=getpass.getuser(),
            rpc_password=gen_password(),
            rpc_use_ssl=False,
            manage_node=True,
            exit_on_close=False,
            active=True,
        )
        profile_db().add(default_profile)
        profile_db().flush()


if __name__ == '__main__':
    import app.helpers
    app.helpers.init_logging()
    from app.models import init_profile_db
    init_profile_db()
    for p in Profile.select().execute():
        print(p)
    p = Profile.select().first()
    p.set_active()
