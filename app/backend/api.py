# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from .rpc import client

log = logging.getLogger(__name__)

class Api:
    def get_balance(self):
        balance = None
        try:
            balance = client.getbalance()['result']
        except Exception as e:
            self.on_rpc_error(str(e))
        return balance

    def get_main_address(self):
        address = None
        try:
            rtp = client.getruntimeparams()
            address = rtp['result']['handshakelocal']
        except Exception as e:
            self.on_rpc_error(str(e))
        return address

    def is_admin(self):
        addresses = None
        try:
            addresses = client.getaddresses()['result']
        except Exception as e:
            self.on_rpc_error(str(e))
        if addresses:
            admin_permissions = None
            try:
                admin_permissions = client.listpermissions(permissions='admin', addresses=addresses)['result']
            except Exception as e:
                self.on_rpc_error(str(e))
            if admin_permissions is not None:
                return len(admin_permissions) > 0
        # If something went wrong return False
        return False

    def is_miner(self):
        addresses = False
        try:
            addresses = client.getaddresses()['result']
        except Exception as e:
            self.on_rpc_error(str(e))
        if addresses:
            mine_permissions = None
            try:
                mine_permissions = client.listpermissions(permissions='mine', addresses=addresses)['result']
            except Exception as e:
                self.on_rpc_error(str(e))
            if mine_permissions is not None:
                return len(mine_permissions) > 0
        # If something went wrong return False
        return False

    def on_rpc_error(self, error):
        log.error(error)

    def get_transactions(self):
        txs = False
        try:
            txs = client.listwallettransactions(10000000)
        except Exception as e:
            self.on_rpc_error(str(e))

        if txs:
            balance = 0
            transactions = []
            for tx in txs['result']:
                if tx['valid']:
                    txid = tx['txid']
                    dt = datetime.fromtimestamp(tx['time'])
                    description = tx.get('comment', '')
                    perm = tx['permissions']
                    if perm:
                        description = 'Skills grant/revoke'

                    items = tx['items']
                    if items:
                        first_item_type = items[0].get('type')
                        if first_item_type == 'stream':
                            description = 'Stream publishing'
                    if tx.get('generated'):
                        description = 'Mining reward'

                    amount = tx['balance']['amount']
                    balance += amount
                    confirmed = tx['confirmations'] > 0
                    transactions.append({
                        'txid': txid,
                        'confirmed': confirmed,
                        'data': ["{}".format(dt), description, "{0:.2f}".format(amount), "{0:.2f}".format(balance)]
                    })
            return transactions
        return False