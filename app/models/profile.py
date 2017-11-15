# -*- coding: utf-8 -*-
import getpass
import logging
import os
import peewee

from decimal import Decimal

import app
from app.helpers import gen_password
from app.models.db import profile_db
from app.signals import signals
from app.backend.rpc import get_active_rpc_client
from app.tools.validators import is_valid_username
from app.exceptions import RpcResponseError, CharmError

log = logging.getLogger(__name__)


class Profile(peewee.Model):
    """Application profile to mangage different Nodes/Accounts"""

    name = peewee.CharField(primary_key=True)
    rpc_host = peewee.CharField()
    rpc_port = peewee.CharField()
    rpc_user = peewee.CharField()
    rpc_password = peewee.CharField()
    rpc_use_ssl = peewee.BooleanField()
    manage_node = peewee.BooleanField()
    exit_on_close = peewee.BooleanField()
    active = peewee.BooleanField()

    # state of variables shown in gui
    alias = peewee.CharField(default='')
    address = peewee.CharField(default='')
    balance = peewee.DecimalField(default=Decimal())
    is_admin = peewee.BooleanField(default=False)
    is_miner = peewee.BooleanField(default=False)

    class Meta:
        database = profile_db

    def __repr__(self):
        return 'Profile(%s, %s, %s...)' % (self.name, self.rpc_host, self.rpc_user)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        signals.profile_changed.emit(self)

    def set_active(self):
        with profile_db.atomic():
            Profile.update(active=False).execute()
            self.active = True
            self.save()

    def update_alias(self, new_alias):
        if not is_valid_username(new_alias):
            raise CharmError(Exception("Invalid Username:\n"
                                       '- It may contain alphanumerical characters and "_", ".", "-"\n'
                                       '- It must not start or end with "-" or "."\n'
                                       '- It must be between 3 and 33 characters\n'
                                       '- It must not have consecutive "_", ".", "-" characters'))

        result = get_active_rpc_client().publish("alias", new_alias, "")
        if result['error']:
            if result['error']['code'] in [-716, -6]:
                raise RpcResponseError(Exception("Insufficient Funds"))
            else:
                raise RpcResponseError(Exception('"Blockchain error: "' + result['error']['message'] + '"'))

    @property
    def data_db_filepath(self):
        """Return database path for this profile"""
        return os.path.join(app.DATA_DIR, self.name + '-data.db')

    @staticmethod
    def get_active() -> 'Profile':
        """Return currently active Pofile"""
        return Profile.select().where(Profile.active).first()

    @staticmethod
    def create_default_profile():
        """Create a default profile for local node connection"""
        log.debug('creating default profile')
        p_obj, created = Profile.get_or_create(
            name=app.DEFAULT_PROFILE_NAME,
            defaults=dict(
                rpc_host=app.DEFAULT_RPC_HOST,
                rpc_port=app.DEFAULT_RPC_PORT,
                rpc_user=getpass.getuser(),
                rpc_password=gen_password(),
                rpc_use_ssl=False,
                manage_node=True,
                exit_on_close=False,
                active=True,
            )
        )
        return p_obj


if __name__ == '__main__':
    import app.helpers
    app.helpers.init_logging()
    from app.models import init_profile_db
    init_profile_db()
    for p in Profile.select().execute():
        print(p)
    p = Profile.select().first()
    p.set_active()
