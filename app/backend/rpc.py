# -*- coding: utf-8 -*-
from decimal import Decimal
import logging
import requests
from config import rpcuser, rpcpassword
from typing import Optional

# Disable SSL warning with self signed certificates
requests.packages.urllib3.disable_warnings()


log = logging.getLogger(__name__)


class RpcClient:

    def __init__(self, host, port, user, pwd, use_ssl=False):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.use_ssl = use_ssl

    ###################
    # RPC API methods #
    ###################

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

    def getinfo(self) -> Optional[dict]:
        return self._call('getinfo')

    def getmultibalances(self) -> Optional[list]:
        result = self._call('getmultibalances')
        data = result['result']
        address_balances = []
        for address in data:
            if address == 'total':
                continue
            for detail in data[address]:
                if detail['assetref'] == "":
                    balance = detail['qty']
                    address_balances.append(
                        (address, balance)
                    )
        return address_balances

    def getnewaddress(self):
        return self._call('getnewaddress')

    def getruntimeparams(self):
        return self._call('getruntimeparams')

    def listaddresses(self, addresses='*', verbose=False, count=100, start=0):
        return self._call('listaddresses', addresses, verbose, count, start)

    def listpermissions(self, permissions='*', addresses='*', verbose=False):
        return self._call('listpermissions', permissions, addresses, verbose)

    def listwallettransactions(self, count=10, skip=0, include_watch_only=False, verbose=False):
        return self._call('listwallettransactions', count, skip, include_watch_only, verbose)

    def send(self, address, amount, comment=None, comment_to=None):
        """
        Note: 'comment' fields are local to the node and not
        publicly embedded in the blockchain transaction.
        """
        return self._call('send', address, amount, comment, comment_to)

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
        response = requests.post(self._url, json=payload, verify=False)
        return response.json(parse_float=Decimal)

client = RpcClient('localhost', 8374, rpcuser, rpcpassword, use_ssl=False)

if __name__ == '__main__':
    from pprint import pprint
    # pprint(client.getaddresses(verbose=True))
    # pprint(client.getbalance())
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

