#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""MultiChain API"""
from datetime import date

from bitcoinrpc.authproxy import AuthServiceProxy
from config import rpcuser, rpcpassword


class Multichain_Api():
    def __init__(self):
        self.connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8374" % (rpcuser, rpcpassword))

    def get_balance(self):
        return self.connection.getbalance()

    def get_balances(self):
        addresses = self.connection.getaddresses()
        balances = []
        multi_balances = self.connection.getmultibalances()
        for address in addresses:
            address_balance = {
                'address': address
            }
            if address in multi_balances:
                address_balance['balance'] = multi_balances[address][0]['qty']
            else:
                address_balance['balance'] = 0
            balances.append(address_balance)
        balances.append({
            'address': 'Total',
            'balance': multi_balances['total'][0]['qty']
        })
        return balances

    def create_address(self):
        # todo: 24 words
        self.connection.getnewaddress()

    def send(self, address, amount, description):
        self.connection.send(address, float(amount), description)

    def get_transactions(self):
        transaction_list = []
        transactions =  self.connection.listwallettransactions(10000)
        for transaction in reversed(transactions):
            transaction_list.append({
                'date': date.fromtimestamp(transaction['time']),
                'amount': transaction['balance']['amount']
            })
        return transaction_list

    def is_admin(self):
        addresses = [entry['address'] for entry in self.connection.listaddresses()]
        return len(self.connection.listpermissions("admin", addresses)) > 0

    def is_miner(self):
        addresses = [entry['address'] for entry in self.connection.listaddresses()]
        return len(self.connection.listpermissions("mine", addresses)) > 0

    def get_miner_info(self):
        miners = self.connection.listpermissions("mine")
        active_miners = []
        actual_block = self.connection.getblockchaininfo()['blocks'] - 1
        # we watch the last 7 * amount of miners blocks for active miner
        last_blocks = self.connection.listblocks("{}-{}".format(actual_block - (7 * len(miners)), actual_block))
        for block in last_blocks:
            address = block['miner']
            if address not in active_miners:
                active_miners.append(address)
        return {
            "miners": miners,
            "active": len(miners) / len(active_miners)
        }

    def get_admin_info(self):
        admins = self.connection.listpermissions("admin")
        active_admins = admins # todo: implement when we have requests

        return {
            "admins": admins,
            "active": len(admins) / len(active_admins)
        }