# -*- coding: utf-8 -*-
import decimal
import json
from decimal import Decimal
import logging
import requests
from typing import Optional
import app


log = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """Custom json encoder that supports Decimal"""
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


class RpcClient:

    def __init__(self, host=None, port=None, user=None, pwd=None, use_ssl=False):
        # from app.backend.models import Profile
        # ap = Profile.get_active()
        self.host = host or app.NODE_RPC_HOST
        self.port = port or app.NODE_RPC_PORT
        self.user = user or app.NODE_RPC_USER
        self.pwd = pwd or app.NODE_RPC_PASSWORD
        self.use_ssl = use_ssl or app.NODE_RPC_USE_SSL

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

    def getaddresses(self, verbose=False):
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
        return self._call('getmultibalances', addresses, assets, minconf, includeWatchOnly, includeLocked )

    def getnewaddress(self):
        return self._call('getnewaddress')

    def getruntimeparams(self):
        return self._call('getruntimeparams')

    def listaddresses(self, addresses='*', verbose=False, count=100, start=0):
        return self._call('listaddresses', addresses, verbose, count, start)

    def listblocks(self, blocks='-4294967295', verbose=False):
        return self._call('listblocks', blocks, verbose)

    def listpermissions(self, permissions='*', addresses='*', verbose=False):
        return self._call('listpermissions', permissions, addresses, verbose)

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
        result = self._call('stop')['result']

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


client = RpcClient()


if __name__ == '__main__':
    from pprint import pprint
    # pprint(client.getaddresses(verbose=True))
    pprint(client.getbalance())
    # pprint(client.getblockchaininfo())
    # pprint(client.getblockchainparams())
    # pprint(client.getinfo())
    # pprint(client.getmultibalances())
    # pprint(client.listwallettransactions(1, verbose=False))
    # pprint(client.getnewaddress())
    # pprint(client.getruntimeparams())
    # pprint(client.listaddresses(verbose=True))
    # pprint(client.validateaddress('1X8meKHXVUpsvgim3q7BJ24Xz7ymSDJnriqt7B'))
    # pprint(client.listpermissions(addresses='1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP', verbose=True))
    # pprint(client.getaddressbalances('1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP'))
    # pprint(client.getmultibalances())
    # pprint(client.getblockcount())
    # pprint(client.liststreamkeys('alias', verbose=True))
