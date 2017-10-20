import base58
from binascii import hexlify, unhexlify
from bitcoin import privtopub, compress
from hashlib import sha256, new

import math

ECDSA_PRIVATE_KEY = '283D01856115B7970B622EAA6DAFF2B9ECE30F1B66927592F6EA70325929102B'

ADDRESS_PUBKEYHASH_VERSION = '00AFEA21'
ADDRESS_CHECKSUM_VALUE = '953ABC69'


def hexxor(a, b):
    result = bytearray()
    for b1, b2 in zip(a, b):
        result.append(b1 ^ b2)
    return bytes(result).hex()


chain_checksum = unhexlify('953ABC69')
address = '1Yu2BuptuZSiBWfr2Qy4aic6qEVnwPWrdkHPEc'
decoded = base58.b58decode(address)
checksum = decoded[-4:]
uncompressed_public_key = privtopub(ECDSA_PRIVATE_KEY)
compressed_public_key = compress(uncompressed_public_key)
pub_key_sha256 = sha256(unhexlify(compressed_public_key)).hexdigest()

ripemd160 = new('ripemd160')
ripemd160.update(unhexlify(pub_key_sha256))
pub_key_rip = ripemd160.hexdigest()

def extend_ripmed(pub_key_rip, ap_version=ADDRESS_PUBKEYHASH_VERSION):
    pkr_data = unhexlify(pub_key_rip)
    ap_version = unhexlify(ap_version)
    steps = math.floor(20 / len(ap_version))
    print(steps)
    chunks = [pkr_data[i:i+steps] for i in range(0, len(pkr_data), steps)]
    merged = b''
    for idx, b in enumerate(unhexlify(ADDRESS_PUBKEYHASH_VERSION), start=0):
        merged += b.to_bytes(1, 'big') + chunks[idx]
    return hexlify(merged).decode()


extended_ripmed = extend_ripmed(pub_key_rip)
pub_key_sha256_2 = sha256(unhexlify(extended_ripmed)).hexdigest()
pub_key_sha256_3 = sha256(unhexlify(pub_key_sha256_2)).hexdigest()
postfix = hexxor(unhexlify(pub_key_sha256_3)[:4], unhexlify(ADDRESS_CHECKSUM_VALUE))
address_bin = extended_ripmed + postfix
address_58 = base58.b58encode(unhexlify(address_bin))

print('Chain-Checksum: ', chain_checksum)
print('Address:     ', address)
print('Decoded:     ', decoded.hex())
print('Checksum:    ', checksum.hex())
print('Un-XOR´d:    ', hexxor(chain_checksum, checksum))
print('PrivKey:     ', ECDSA_PRIVATE_KEY)
print('PubKey:      ', uncompressed_public_key)
print('PubKey comp: ', compressed_public_key)
print('PubKey sha:  ', pub_key_sha256)
print('PubKey rip:  ', pub_key_rip)
print('Extended rip:', extended_ripmed)
print('PubKey sha 2:', pub_key_sha256_2)
print('PubKey sha 3:', pub_key_sha256_3)
print('Postfix:     ', postfix)
print('Address bin: ', address_bin)
print('Address 58:  ', address_58)
