# -*- coding: utf-8 -*-
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

    def getbalance(self) -> Optional[float]:
        result = self._call('getbalance')
        if result is not None:
            return result.json()['result']

    def getblockchaininfo(self) -> Optional[dict]:
        result = self._call('getblockchaininfo')
        if result is not None:
            return result.json()

    def getinfo(self) -> Optional[dict]:
        result = self._call('getinfo')
        if result is not None:
            return result.json()

    def stop(self) -> Optional[str]:
        result = self._call('stop')
        if result is not None:
            return result.json()['result']

    ####################
    # Internal helpers #
    ####################

    @property
    def _url(self) -> str:
        url = '{}:{}@{}:{}'.format(self.user, self.pwd, self.host, self.port)
        return 'https://' + url if self.use_ssl else 'http://' + url

    def _call(self, method, params=None) -> Optional[requests.Response]:
        params = [] if params is None else params
        payload = {"method": method, "params": params}
        try:
            response = requests.post(self._url, json=payload, verify=False)
        except requests.exceptions.RequestException as e:
            response = None
            log.error(e)
        return response

client = RpcClient('localhost', 8374, rpcuser, rpcpassword, use_ssl=False)

if __name__ == '__main__':
    from pprint import pprint
    print(client.getbalance())
    pprint(client.getblockchaininfo())
    pprint(client.getinfo())
