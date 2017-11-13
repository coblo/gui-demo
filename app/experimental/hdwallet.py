"""HD Wallet experimentation.

Compare against ledger HD wallet derivations:

https://www.ledgerwallet.com/support/bip39-standalone.html

See also:
https://github.com/satoshilabs/slips/blob/master/slip-0044.md
https://en.bitcoin.it/wiki/List_of_address_prefixes
https://github.com/libbitcoin/libbitcoin/wiki/Altcoin-Version-Mappings
https://bitcore.io/playground/#/address
https://brainwalletx.github.io/#generator
https://bitcoin.stackexchange.com/a/53579

bitcoin bip32 private key: b'\x04\x88\xAD\xE4'
"""
import mnemonic
from binascii import hexlify
from pycoin.key.BIP32Node import BIP32Node
from pycoin.networks.network import Network
from pycoin.networks import register_network
import bitcoin
from pycoin.serialize import h2b
from pycoin.tx.Tx import Tx as CharmTx
from pycoin.block import Block as CharmBlock

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


"""
Charm Testnet:
network-message-start = f4f3e3fa  
default-network-port = 8375
address-checksum-value	d8a558e6
address-pubkeyhash-version	0046e454
address-scripthash-version	054b9e59

DEFAULT_ARGS_ORDER = (
    'code', 'network_name', 'subnet_name',
    'wif', 'address', 'pay_to_script', 'prv32', 'pub32',
    'tx', 'block',
    'magic_header', 'default_port', 'dns_bootstrap',
    'address_wit', 'pay_to_script_wit',
    'bech32_hrp'
)
"""


charm = Network(
    'CHM', "charm", "testnet",
    h2b('807C3B9F'), h2b('0046E454'), h2b('054B9E59'), h2b("0488ADE4"), h2b("0488B21E"),
    CharmTx, CharmBlock,
    h2b('F4F3E3FA'), 8375, [],
    bech32_hrp='ch'
)

register_network(charm)


def ecdsa_key_from_seed(seed, netcode, coinid):
    bip32_root_key = BIP32Node.from_master_secret(seed, netcode)
    main_handshake_key = bip32_root_key.subkey_for_path('44H/{}H/0H/0/0'.format(coinid))
    ecdsa_private_key = hex(main_handshake_key.secret_exponent())[2:]
    return ecdsa_private_key


print('ecdsa_key_from_seed BTC: ', ecdsa_key_from_seed(seed, 'BTC', 0))
print('ecdsa_key_from_seed CHM: ', ecdsa_key_from_seed(seed, 'CHM', 0))



