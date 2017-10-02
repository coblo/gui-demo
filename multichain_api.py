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