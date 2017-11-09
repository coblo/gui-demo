# -*- coding: utf-8 -*-
"""High level api functions for reading and writing blockchain data."""
from binascii import hexlify, unhexlify
from typing import Optional, NewType, List
from decimal import Decimal
import ubjson

from app.backend.rpc import get_active_rpc_client
from app.enums import Permission


TxId = NewType('TxID', str)
Form = NewType('Form', dict)


# TODO define and implement highlevel api


def pay(to_address: str, amount: Decimal, comment: str, fee: Decimal=Decimal('0.0001')) -> Optional[TxId]:
    pass


def register_alias(alias: str) -> Optional[TxId]:
    pass


def apply_for(perm: Permission, form: Form) -> Optional[TxId]:
    pass


# timestamp api


def put_timestamp(hexhash: str, comment: str='', stream='test') -> Optional[TxId]:

    client = get_active_rpc_client()

    if comment:
        data = dict(comment=comment)
        data_hex = hexlify(ubjson.dumpb(data)).decode('utf8')
        response = client.publish(stream, hexhash, data_hex)
    else:
        response = client.publish(stream, hexhash)
    print(response)
    return TxId(response['result'])


def get_timestamps(hash_value: str, stream='test') -> Optional[List]:
    client = get_active_rpc_client()
    response = client.liststreamkeyitems(stream, hash_value, verbose=True, count=1000, start=-1000)
    result = response['result']
    timestamps = []
    for entry in result:
        if entry['data']:
            data = ubjson.loadb(unhexlify(entry['data']))
            comment = data.get('comment', '')
        else:
            comment = ''

        for publisher in entry['publishers']:
            timestamps.append((entry['time'], publisher, comment))
    return timestamps


if __name__ == '__main__':
    from pprint import pprint
    import app
    app.init()
    client = get_active_rpc_client()
    # pprint(client.publish('test', 'key only'))

    # pprint(
    #     put_timestamp('a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e', 'An update')
    # )
    # pprint(client.liststreamkeyitems('test', 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e', verbose=True))
    pprint(get_timestamps('a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e', 'test'))
