# -*- coding: utf-8 -*-
"""High level api functions for reading and writing blockchain data."""
import logging
import ubjson
from binascii import hexlify, unhexlify
from typing import Optional, NewType, List

from app.backend.rpc import get_active_rpc_client
from app.exceptions import RpcResponseError

log = logging.getLogger(__name__)


TxId = NewType('TxID', str)
Form = NewType('Form', dict)


# TODO define and implement highlevel api


# def pay(to_address: str, amount: Decimal, comment: str, fee: Decimal=Decimal('0.0001')) -> Optional[TxId]:
#     pass
#
#
# def register_alias(alias: str) -> Optional[TxId]:
#     pass
#
#
# def apply_for(perm: Permission, form: Form) -> Optional[TxId]:
#     pass


# timestamp api


def put_timestamp(hexhash: str, comment: str='', stream='timestamp') -> Optional[TxId]:

    client = get_active_rpc_client()

    if comment:
        data = dict(comment=comment)
        serialized = ubjson.dumpb(data)
        data_hex = hexlify(serialized).decode('utf-8')
        response = client.publish(stream, hexhash, data_hex)
    else:
        response = client.publish(stream, hexhash)

    if response['error'] is not None:
        raise RpcResponseError(response['error']['message'])

    return TxId(response['result'])




def get_publisher_timestamps(address:str, stream='timestamp'):
    response = get_active_rpc_client().liststreampublisheritems(stream, address, verbose=True, count=1000, start=-1000)
    if response['error'] is not None:
        raise RpcResponseError(response['error']['message'])

    result = response['result']
    timestamps = []
    for entry in reversed(result):
        if entry['data']:
            if not isinstance(entry['data'], str):
                log.warning('Stream item data is not a string: %s' % entry['data'])
                # Todo investigate dict with size, txid, vout in stream item data
                continue
            data = ubjson.loadb(unhexlify(entry['data']))
            comment = data.get('comment', '')
        else:
            comment = ''
        timestamps.append((entry['time'], entry['key'], comment))

    return timestamps


if __name__ == '__main__':
    import app
    app.init()
