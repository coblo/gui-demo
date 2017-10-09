#!/usr/bin/python3
# -*- coding: utf-8 -*-

from OpenSSL import crypto
from os.path import exists, join

CERT_FILE = "server.cert"
KEY_FILE = "server.pem"


def create_self_signed_cert(cert_dir):
    """
    If server.cert and server.pem don't exist in cert_dir, create a new
    self-signed cert and keypair and write them into that directory.
    cert_dir should be set to the multichain data directory.
    """

    if not exists(join(cert_dir, CERT_FILE)) \
            or not exists(join(cert_dir, KEY_FILE)):
        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        cert.get_subject().L = "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        cert.get_subject().O = "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
        cert.get_subject().OU = "my organization"
        cert.get_subject().CN = "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')

        open(join(cert_dir, CERT_FILE), "wt").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
        open(join(cert_dir, KEY_FILE), "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode('utf-8'))


create_self_signed_cert(".")
