"""HD Wallet experimentation.

Compare against ledger HD wallet derivations:

https://www.ledgerwallet.com/support/bip39-standalone.html

See also:
https://github.com/satoshilabs/slips/blob/master/slip-0044.md
https://en.bitcoin.it/wiki/List_of_address_prefixes
https://github.com/libbitcoin/libbitcoin/wiki/Altcoin-Version-Mappings

bitcoin bip32 private key: b'\x04\x88\xAD\xE4'
"""
import mnemonic
from binascii import hexlify
from pycoin.key.BIP32Node import BIP32Node
import bitcoin


m = mnemonic.Mnemonic('english')
# words = m.generate(256)

# A sample 24 word mnemonic
words = 'december tobacco prize tunnel mammal mixture attend clap jeans inch hybrid apple suspect tube library soap trick scatter wise accident obvious wash alarm fire'
print('Words: ', words)

entropy = m.to_entropy(words)
print('Entropy: ', hexlify(entropy))

seed = m.to_seed(words)
print('Bip39 Seed: ', hexlify(seed))

bip32_root_key = bitcoin.bip32_master_key(seed, b'\x04\x88\xAD\xE4')
print('BIP32 Root Key (bitcoin lib): ', bip32_root_key)

# TODO pycoin allows us to register our own network instead of using BTC.
wallet = BIP32Node.from_master_secret(seed, 'BTC')
print('BIP32 Root Key (pycoin lib): ', wallet.as_text(as_private=True))

# derivation path semantics are purpose/coin/account/external-or-internal/address-index (H for hardened)
# - purpose: 44 indicates BIP44 derivation
# - coin: 0 is bitcoin, 1 is testnent (all coins).
#         We should register here:
#         https://github.com/satoshilabs/slips/blob/master/slip-0044.md
# - account: 0 is the first account
# - external-or-internal: 0 for external 1 for internal change addresses
# - address-index: 0 first address in derivation path
print('Fist (main) address: ', wallet.subkey_for_path('44H/0H/0H/0/0').address())
handshake = wallet.subkey_for_path('44H/0H/0H/0/0')
pubkey = handshake.sec_as_hex()
print('Public Key', pubkey)
print('Wif', handshake.wif(use_uncompressed=False))
print('bitcoin lib decoded Wif', bitcoin.decode_privkey(handshake.wif()))
print('pycoin lib secret exponent', handshake.secret_exponent())
priv_key = hex(handshake.secret_exponent())[2:]
print('private key for our address generation: ', priv_key)


def ecdsa_key_from_seed(seed):
    bip32_root_key = BIP32Node.from_master_secret(seed, 'BTC')
    main_handshake_key = bip32_root_key.subkey_for_path('44H/0H/0H/0/0')
    ecdsa_private_key = hex(main_handshake_key.secret_exponent())[2:]
    return ecdsa_private_key


print('ecdsa_key_from_seed: ', ecdsa_key_from_seed(seed))
