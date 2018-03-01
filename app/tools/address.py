# -*- coding: utf-8 -*-
"""Address Management"""
from hashlib import sha256, new
from binascii import unhexlify
from bitcoin import privtopub, compress
from mnemonic import Mnemonic
import base58
from pycoin.key.BIP32Node import BIP32Node
import app


MAIN_BIP44_PATH_TESTNET = '44H/1H/0H/0/0'


def main_address_from_mnemonic(words: str, pkhv=app.TESTNET_ADDRESS_PUBKEYHASH_VERSION, cv=app.TESTNET_ADDRESS_CHECKSUM_VALUE) -> str:
    """Returns the main address from a 24 word mnemonic (Testnet only).

    The main address is the first address in the BIP44 derivation path.
    We use it as our handshakelocal address in the node.
    :param str words: BIP-0039 - 24 word mnemonic
    :return str: multichain encoded testnet address for handshake local
    """
    priv_key = ecdsa_pk_from_mnemonic(words)
    return create_address(
        priv_key,
        pkhv,
        cv,
    )


def main_wif_from_mnemonic(words: str) -> str:
    """Returns wif encoded private key of main address from a
    24 word mnemonic (Testnet only).

    The main address is the first address in the BIP44 derivation path.
    We use it as our handshakelocal address in the node.
    :param str words: BIP-0039 - 24 word mnemonic
    :return str: multichain encoded wif private key for handshake local
    """
    priv_key = ecdsa_pk_from_mnemonic(words)
    return create_wif(
        priv_key,
        app.TESTNET_PRIVATE_KEY_VERSION,
        app.TESTNET_ADDRESS_CHECKSUM_VALUE,
    )


def ecdsa_pk_from_mnemonic(words: str) -> str:
    """
    Returns the hex encoded ecdsa private key for the main address
    from a 24 word mnemonic.

    The main address is the first address in the BIP44 derivation path.
    We use it as our handshakelocal address in the node.

    :param str words: BIP-0039 - 24 word mnemonic
    :return str: hex encoded ecdsa private key
    """
    seeder = Mnemonic('english')
    bip_39_seed = seeder.to_seed(words)
    # This currently uses BTC Network settings
    bip_32_root_key = BIP32Node.from_master_secret(bip_39_seed, 'BTC')
    main_address_key = bip_32_root_key.subkey_for_path(MAIN_BIP44_PATH_TESTNET)
    ecdsa_private_key = hex(main_address_key.secret_exponent())[2:]
    return ecdsa_private_key


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
    return public_key_to_address(pubkey, pkhv, cv)


def create_wif(private_key, pkv, acv, compressed=True):
    """Create a 'Wallet Import Format' encoded private key.

    Implementation of http://bit.ly/2hH1UUY

    :param str private_key: ECDSA private key (hex)
    :param str pkv: private-key-version of chain (hex)
    :param str acv: address-checksum-value of chain (hex)
    :param bool compressed: build address with compressed pubkey
    :return str: wif encoded private_key
    """
    if compressed:
        privkey = private_key + '01'
    else:
        privkey = private_key

    privkey_raw = bytearray(unhexlify(privkey))
    pkv_raw = bytearray(unhexlify(pkv))
    acv_raw = unhexlify(acv)

    # Extend:
    steps = 33 // len(pkv_raw)
    idx = 0
    for pkv_byte in pkv_raw:
        privkey_raw.insert(idx, pkv_byte)
        idx += steps + 1

    privkey_raw_extended = bytes(privkey_raw)
    privkey_raw_sha256d = sha256d(privkey_raw_extended)

    postfix = xor_bytes(privkey_raw_sha256d[:4], acv_raw)

    # Compose final WIF
    wif_bin = privkey_raw_extended + postfix
    return base58.b58encode(wif_bin)


def public_key_to_address(public_key: str, pkhv, cv):
    """Create Address from a public key.

    Implementation of http://bit.ly/2hH1UUY

    :param str public_key: hex encoded ECDSA public key
    :param str pkhv: address-pubkeyhash-version of chain
    :param str cv: address-checksum-value of chain
    :return str: address
    """

    # Work with raw bytes
    pubkey_raw = unhexlify(public_key)
    pkhv_raw = unhexlify(pkhv)
    cv_raw = unhexlify(cv)

    # Hash public key
    ripemd160 = new('ripemd160')
    ripemd160.update(sha256(pubkey_raw).digest())
    pubkey_raw_hashed = ripemd160.digest()

    # Extend
    steps = 20 // len(pkhv_raw)
    idx = 0
    privkey_ba = bytearray(pubkey_raw_hashed)
    for pkhv_byte in pkhv_raw:
        privkey_ba.insert(idx, pkhv_byte)
        idx += steps + 1
    pubkey_raw_extended = bytes(privkey_ba)

    pubkey_raw_sha256d = sha256d(pubkey_raw_extended)

    # XOR first 4 bytes with address-checksum-value for postfix
    postfix = xor_bytes(pubkey_raw_sha256d[:4], cv_raw)

    # Compose final address
    address_bin = pubkey_raw_extended + postfix
    return base58.b58encode(address_bin)


def address_valid(address, checksum_value="00000000"):
    """Validate a chain specific address.

    :param str address: chain specific address or wif encoded private key
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
        compressed=True
    ) == '1Yu2BuptuZSiBWfr2Qy4aic6qEVnwPWrdkHPEc'

    assert address_valid(
        '1Yu2BuptuZSiBWfr2Qy4aic6qEVnwPWrdkHPEc',
        ADDRESS_CHECKSUM_VALUE
    ) is True

    assert address_valid(
        '1HrciBAMdcPbSfDoXDyDpDUnb44Dg8sH4WfVyP',
        'd8a558e6',
    )

    assert create_wif(
        private_key='B69CA8FFAE36F11AD445625E35BF6AC57D6642DDBE470DD3E7934291B2000D78',
        pkv='8025B89E',
        acv='7B7AEF76',
        compressed=True
    ) == 'VEEWgYhDhqWnNnDCXXjirJYXGDFPjH1B8v6hmcnj1kLXrkpxArmz7xXw'

    assert address_valid(
        'VEEWgYhDhqWnNnDCXXjirJYXGDFPjH1B8v6hmcnj1kLXrkpxArmz7xXw',
        '7B7AEF76',
    )

    assert ecdsa_pk_from_mnemonic(
        'december tobacco prize tunnel mammal mixture '
        'attend clap jeans inch hybrid apple '
        'suspect tube library soap trick scatter '
        'wise accident obvious wash alarm fire'
    ) == 'ccffdefc1cf59552d44bb40098d9aa0c8bbc355ee71eac6776715be1ba209d5e'
