# -*- coding: utf-8 -*-
"""High level api functions for reading and writing blockchain data."""
import logging
import ubjson
from binascii import hexlify, unhexlify
from typing import Optional, NewType, List

import app
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


def put_timestamp(hexhash: str, comment: str='', stream=app.STREAM_TIMESTAMP) -> Optional[TxId]:

    client = get_active_rpc_client()

    try:
        if comment:
            data = dict(comment=comment)
            serialized = ubjson.dumpb(data)
            data_hex = hexlify(serialized).decode('utf-8')
            response = client.publish(stream, hexhash, data_hex)
        else:
            response = client.publish(stream, hexhash, "")
        return TxId(response)

    except Exception as e:
        log.debug(e)
        raise RpcResponseError(str(e))


if __name__ == '__main__':
    import app
    app.init()
