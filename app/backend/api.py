# -*- coding: utf-8 -*-
from .rpc import RpcClient
from config import rpcuser, rpcpassword

class Api:
    def __init__(self):
        self.rps_client = RpcClient('localhost', 8374, rpcuser, rpcpassword, use_ssl=False)

    def get_balance(self):
        return self.rps_client.getbalance()

    def is_admin(self):
        addresses = self.rps_client.getaddresses()['result']
        return len(self.rps_client.listpermissions(permissions='admin', addresses=addresses)['result']) > 0

    def is_miner(self):
        addresses = self.rps_client.getaddresses()['result']
        return len(self.rps_client.listpermissions(permissions='mine', addresses=addresses)['result']) > 0