# -*- coding: utf-8 -*-
"""Address Management"""
from hashlib import sha256, new
from binascii import unhexlify
from bitcoin import privtopub, compress
import base58


def create_address(private_key, pkhv, cv, compressed=True):
    """Create Address from ECDSA private key.

    Implementation of http://bit.ly/2hH1UUY

    :param str private_key: ECDSA private key
    :param str pkhv: address-pubkeyhash-version of chain
    :param str cv: address-checksum-value of chain
    :param bool compressed: build address with compressed pubkey
    :return str: address
    """
    # Derive public key
    pubkey = privtopub(private_key)
    if compressed:
        pubkey = compress(pubkey)

    # Work with raw bytes
    pubkey_raw = unhexlify(pubkey)
    pkhv_raw = unhexlify(pkhv)
    cv_raw = unhexlify(cv)

    # Hash public key
    ripemd160 = new('ripemd160')
    ripemd160.update(sha256(pubkey_raw).digest())
    pubkey_raw_hashed = ripemd160.digest()

    # Extend
    steps = 20 // len(pkhv_raw)
    chunks = [pubkey_raw_hashed[i:i+steps] for i in range(0, len(pubkey_raw_hashed), steps)]
    pubkey_raw_extended = b''
    for idx, b in enumerate(unhexlify(ADDRESS_PUBKEYHASH_VERSION), start=0):
        pubkey_raw_extended += b.to_bytes(1, 'big') + chunks[idx]

    # Double SHA256
    pubkey_raw_sha256d = sha256d(pubkey_raw_extended)

    # XOR first 4 bytes with address-checksum-value for postfix
    postfix = xor_bytes(pubkey_raw_sha256d[:4], cv_raw)

    # Compose final address
    address_bin = pubkey_raw_extended + postfix
    return base58.b58encode(address_bin)


def address_valid(address, checksum_value="d8a558e6"):
    """Validate a chain specific address.

    :param str address:
    :param str checksum_value: chain param address-checksum-value (4 bytes hex)
    :return bool:
    """
    try:
        decoded = base58.b58decode(address)
    except Exception:
        return False

    prefix = decoded[:-4]
    postfix = decoded[-4:]
    checksum = xor_bytes(postfix, unhexlify(checksum_value))
    if sha256d(prefix)[:4] == checksum:
        return True

    return False


def sha256d(data):
    return sha256(sha256(data).digest()).digest()


def xor_bytes(a, b):
    result = bytearray()
    for b1, b2 in zip(a, b):
        result.append(b1 ^ b2)
    return bytes(result)


if __name__ == '__main__':
    """Test module when executed as a script.
    
    Test vectors are from: http://bit.ly/2hH1UUY
    """

    ADDRESS_PUBKEYHASH_VERSION = '00AFEA21'
    ADDRESS_CHECKSUM_VALUE = '953ABC69'

    assert create_address(
        '283D01856115B7970B622EAA6DAFF2B9ECE30F1B66927592F6EA70325929102B',
        ADDRESS_PUBKEYHASH_VERSION,
        ADDRESS_CHECKSUM_VALUE,
    ) == '1Yu2BuptuZSiBWfr2Qy4aic6qEVnwPWrdkHPEc'

    assert address_valid(
        '1Yu2BuptuZSiBWfr2Qy4aic6qEVnwPWrdkHPEc',
        ADDRESS_CHECKSUM_VALUE
    ) is True

    assert address_valid(
        '1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP',
        "d8a558e6",
    )
