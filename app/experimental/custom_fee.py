# -*- coding: utf-8 -*-
"""Create a transaction with custom fees"""
from app.backend.rpc import client

from_addr = "1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP"
to_addr = "1Lr3zphEuSJx9xMtnB6RRRfZbknGFDf7JEsgk1"

payment = {to_addr: 0.1}
fee = 0.01

# this must be unspent output (listunspent) that is not a coinbase transaction
inputs = [{
    "txid": "debc9d4d720abc1938a2dc31c7715d657f895a3f6cbcd34b6e784bcb220d8811",
    "vout": 1
}]

rtx = client.createrawtransaction(inputs, payment)['result']
print(rtx)
raw_tx_with_fee = client.appendrawchange(rtx, from_addr, fee)['result']
print(raw_tx_with_fee)
signed_tx = client.signrawtransaction(raw_tx_with_fee)['result']['hex']
print(signed_tx)
sent = client.sendrawtransaction(signed_tx)
print(sent)


