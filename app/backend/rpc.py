# -*- coding: utf-8 -*-
import decimal
import json
import logging
import requests
from decimal import Decimal
from typing import Optional
# Don´t remove this import. Its a hack for cx freezing
from multiprocessing import Queue


log = logging.getLogger(__name__)


def get_active_rpc_client():
    from app.models import Profile
    profile = Profile.get_active()
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


class RpcClient:

    def __init__(self, host=None, port=None, user=None, pwd=None, use_ssl=False):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.use_ssl = use_ssl

    ###################
    # RPC API methods #
    ###################

    def appendrawchange(self, tx_hex, address, native_fee=0.0001):
        return self._call('appendrawchange', tx_hex, address, native_fee)

    def createrawtransaction(self, inputs, payment, data=(), action=''):
        return self._call('createrawtransaction', inputs, payment, data, action)

    def createrawsendfrom(self, from_addr, to, data=tuple(), action=""):
        return self._call('createrawsendfrom', from_addr, to, data, action)

    def decoderawtransaction(self, tx_hex):
        return self._call('decoderawtransaction', tx_hex)

    def getaddresses(self, verbose=True):
        return self._call('getaddresses', verbose)

    def getaddressbalances(self, address, minconf=1, includelocked=False):
        return self._call('getaddressbalances', address, minconf, includelocked)

    def getbalance(self):
        return self._call('getbalance')

    def getblockchaininfo(self) -> Optional[dict]:
        return self._call('getblockchaininfo')

    def getblockchainparams(self):
        return self._call('getblockchainparams')

    def getblockhash(self, height):
        return self._call('getblockhash', height)

    def getblockcount(self):
        return self._call('getblockcount')

    def getinfo(self) -> Optional[dict]:
        return self._call('getinfo')

    def getmultibalances(self, addresses='*', assets='*', minconf=0, includeWatchOnly=False, includeLocked=False):
        return self._call('getmultibalances', addresses, assets, minconf, includeWatchOnly, includeLocked)

    def getnewaddress(self):
        return self._call('getnewaddress')

    def getruntimeparams(self):
        return self._call('getruntimeparams')

    def listaddresses(self, addresses='*', verbose=True, count=100, start=0):
        return self._call('listaddresses', addresses, verbose, count, start)

    def listblocks(self, blocks='-3', verbose=True):
        return self._call('listblocks', blocks, verbose)

    def listpermissions(self, permissions='*', addresses='*', verbose=True):
        return self._call('listpermissions', permissions, addresses, verbose)

    def liststreamitems(self, stream, verbose=False, count=10000000, start=0, local_ordering=False):
        return self._call('liststreamitems', stream, verbose, count, start, local_ordering)

    def liststreamkeys(self, stream, keys='*', verbose=False, count=10000000, start=0, local_ordering=False):
        return self._call('liststreamkeys', stream, keys, verbose, count, start, local_ordering)

    def listwallettransactions(self, count=10, skip=0, include_watch_only=False, verbose=False):
        return self._call('listwallettransactions', count, skip, include_watch_only, verbose)

    def publish(self, stream, key, data):
        return self._call('publish', stream, key, data)

    def send(self, address, amount, comment=None, comment_to=None):
        """
        Note: 'comment' fields are local to the node and not
        publicly embedded in the blockchain transaction.
        """
        return self._call('send', address, amount, comment, comment_to)

    def signrawtransaction(self, tx_hex):
        return self._call('signrawtransaction', tx_hex)

    def sendrawtransaction(self, tx_hex):
        return self._call('sendrawtransaction', tx_hex)

    def stop(self) -> Optional[str]:
        return self._call('stop')['result']

    def validateaddress(self, address):
        return self._call('validateaddress', address)

    ####################
    # Internal helpers #
    ####################

    @property
    def _url(self) -> str:
        url = '{}:{}@{}:{}'.format(self.user, self.pwd, self.host, self.port)
        return 'https://' + url if self.use_ssl else 'http://' + url

    def _call(self, method, *args) -> Optional[requests.Response]:
        args = [arg for arg in args if arg is not None]
        payload = {"id": method, "method": method, "params": args}
        serialized = json.dumps(payload, cls=DecimalEncoder)
        response = requests.post(self._url, data=serialized, verify=False)
        return response.json(parse_float=Decimal)


if __name__ == '__main__':
    from pprint import pprint
    from app import helpers
    from app import models
    helpers.init_logging()
    helpers.init_data_dir()
    models.init_profile_db()
    helpers.init_node_data_dir()
    models.init_data_db()
    print(models.Profile.get_active())
    client = get_active_rpc_client()

    # pprint(client.getaddresses(verbose=True))
    # pprint(client.getbalance())
    # pprint(client.getblockchaininfo())
    # pprint(client.getblockchainparams())
    # pprint(client.getinfo())
    # pprint(client.getmultibalances())
    # pprint(client.listwallettransactions(10000, verbose=False))
    # pprint(client.getnewaddress())
    # pprint(client.getruntimeparams())
    # pprint(client.listaddresses(verbose=True))
    # pprint(client.validateaddress('1X8meKHXVUpsvgim3q7BJ24Xz7ymSDJnriqt7B'))
    # pprint(client.listpermissions(addresses='1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP', verbose=True))
    # pprint(client.getaddressbalances('1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP'))
    # pprint(client.getmultibalances())
    # pprint(client.getblockcount())
    # pprint(client.liststreamkeys('alias'))
    pprint(client.liststreamitems('alias', start=1, count=3))
