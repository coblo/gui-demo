# -*- coding: utf-8 -*-
import logging
from collections import namedtuple
from decimal import Decimal
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

    def get_addresses(self):
        balances = []
        multi_balances = None
        addresses = None
        try:
            multi_balances = client.getmultibalances()['result']
            addresses = client.getaddresses()['result']
        except Exception as e:
            self.on_rpc_error(str(e))
        if addresses is not None:
            for address in addresses:
                address_balance = {
                    'Address': address
                }
                if address in multi_balances:
                    address_balance['Balance'] = multi_balances[address][0]['qty']
                else:
                    address_balance['Balance'] = Decimal(0)
                balances.append(address_balance)
            balances.append({
                'Address': 'Total',
                'Balance': multi_balances['total'][0]['qty']
            })
            return balances
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
                    confirmations = tx['confirmations']
                    transactions.append(
                        Transaction(dt, description, amount, balance, confirmations, txid)
                    )
            transactions.reverse()
            return transactions
        return False

    def send(self, address, amount, description=None):
        try:
            success = client.send(address, amount, description)
        except Exception as e:
            self.on_rpc_error(str(e))
            return False
        return success['error'] is None

    def get_actual_hash(self):
        actual_hash = None
        try:
            actual_block = client.getblockchaininfo()['result']['blocks'] - 1
            actual_hash = client.getblockhash(actual_block)['result']
        except Exception as e:
            self.on_rpc_error(str(e))
        return actual_hash


class Transaction(namedtuple('Transaction', 'datetime description amount balance confirmations txid')):
    pass
