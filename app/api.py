# -*- coding: utf-8 -*-
"""High level api functions for reading and writing blockchain data."""
import logging
from binascii import hexlify, unhexlify
from typing import Optional, NewType, List
from decimal import Decimal
import ubjson
from PyQt5.QtWidgets import QMessageBox, QWidget

from app.backend.rpc import get_active_rpc_client
from app.enums import Permission


log = logging.getLogger(__name__)


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


def put_timestamp(hexhash: str, comment: str='', stream='timestamp') -> Optional[TxId]:

    client = get_active_rpc_client()

    if comment:
        data = dict(comment=comment)
        data_hex = hexlify(ubjson.dumpb(data)).decode('utf8')
        response = client.publish(stream, hexhash, data_hex)
    else:
        response = client.publish(stream, hexhash)

    # Todo raise custom RPC Error if response contains an error code/message

    return TxId(response['result'])


def get_timestamps(hash_value: str, stream='timestamp') -> Optional[List]:
    client = get_active_rpc_client()
    response = client.liststreamkeyitems(stream, hash_value, verbose=True, count=1000, start=-1000)
    if response['error'] is None:
        result = response['result']
        timestamps = []
        for entry in result:
            if entry['data']:
                if not isinstance(entry['data'], str):
                    log.warning('Stream item data is not a string: %s' % entry['data'])
                    # Todo investigate dict wit size, txid, vout in stream item data
                    continue
                data = ubjson.loadb(unhexlify(entry['data']))
                comment = data.get('comment', '')
            else:
                comment = ''

            for publisher in entry['publishers']:
                timestamps.append((entry['time'], publisher, comment))
        return timestamps
    else:
        QMessageBox.warning(QWidget(), 'Error reading timestamp stream', response['error']['message'])
        return None


if __name__ == '__main__':
    import app
    app.init()
