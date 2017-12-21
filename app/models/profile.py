# -*- coding: utf-8 -*-
import getpass
import logging
import os
from decimal import Decimal

from sqlalchemy import String, Column, Boolean, Float
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declarative_base

import app
from app.helpers import gen_password
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

    @property
    def data_db_filepath(self):
        """Return database path for this profile"""
        return os.path.join(app.DATA_DIR, self.name + '-data.db')

    @staticmethod
    def get_active(profile_db) -> 'Profile':
        """Return currently active Pofile"""
        return profile_db.query(Profile).filter(Profile.active).first()

    @staticmethod
    def create_default_profile(profile_db): # todo: ungetestet
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
        profile_db.add(default_profile)


@listens_for(Profile, "after_update")
@listens_for(Profile, "after_insert")
def after_update(mapper, connection, profile):
    signals.profile_changed.emit(profile)


if __name__ == '__main__':
    import app.helpers
    from app.models import init_profile_db
    from app.models.db import profile_session_scope
    app.helpers.init_logging()

    init_profile_db()
    with profile_session_scope() as session:
        for p in session.query(Profile).all():
            print(p)

        p = session.query(Profile).first()
        p.active = True
