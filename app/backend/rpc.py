# -*- coding: utf-8 -*-
import decimal
import json
import logging
from mcrpc import RpcClient
# Don´t remove this import. Its a hack for cx freezing
from multiprocessing import Queue

from app.signals import signals

log = logging.getLogger(__name__)


def get_active_rpc_client(override=None):
    from app.models import Profile
    from app.models.db import profile_session_scope
    with profile_session_scope() as session:
        profile = override or Profile.get_active(session)
    assert isinstance(profile, Profile)
    return RpcClient(
        profile.rpc_host, profile.rpc_port, profile.rpc_user, profile.rpc_password, profile.rpc_use_ssl
    )


class DecimalEncoder(json.JSONEncoder):
    """Custom json encoder that supports Decimal"""
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


if __name__ == '__main__':
    from pprint import pprint
    import app
    from app.models import Profile
    from app.models.db import profile_session_scope
    app.init()
    with profile_session_scope() as session:
        print(Profile.get_active(session))
    client = get_active_rpc_client()
    # pprint(client.getmultibalances('*', '*', 1, False, False))
    # pprint(client.getmultibalances('*', '*', 0, False, True))
    print(client.getbestblockhash())
    pprint(client.listwallettransactions(1))
