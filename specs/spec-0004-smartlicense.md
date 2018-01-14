---
Spec: 4
Title: Smart Licenses
Author: Titusz <tp@py7.de>
Status: Raw
Created: 2018-01-12
License: BSD-2-Clause
---

# Smart Licenses

## Purpose

Allow content owners to offer, sell and verify content lincenses via blockchain. 
This document specifies an open stream named `smartlicense` and the associated 
data structures and transaction models that can be used to publish and verify 
machine readable licenses and contracting rules.git 

## Schema

The smartlicense-stream is readable and writable by every blockchain 
participant. An SmartLicense is identified by a publisher provided 
UUID Version 4. See [smartlicense.proto](../smartlicense/smartlicense.proto)
for current state of data structure for SmartLicenses.

## Transaction Models

### Attestation Example

This is an example that demostrates attestation based licensing process.

#### Creating an attestion based SmartLicense

A publisher creates a SmartLicense with a frontend application. The 
application then creates an encoded version of the data collected from the 
user. A minimal JSON-encoded SmartLicense looks like this:

```json
{
  	"materials": ["2EvGugzdGh5Zp-2LpzWi7kt2kUA-2LpprH51GMPhq-2VhLRzBEdDLa4"],
  	"activation_modes": ["ON_CHAIN_ATTESTATION"]
}
```

In this example the `licensors` and the `payment_address` fields are not 
explicitly specified. Both will be set  to the **Wallet-ID** of the entity 
that published the SmartLicense to the blockchain. The application also 
generates a **UUID4** as identifier for a specific SmartLicense. The 
application publishes the SmartLicense as a multichain stream-item signed by 
the publisher to the `smartlicense` stream with the **UUID4** as key and the 
SmartLicense as data. The data is published in a compact binary encoding 
(protobuf).

#### Issuing  a License to a user

The publisher registers an entry in the  `smartlicense_attestation` - stream 
with the **Wallet-ID** of the user as key and the **SmartLicense UUID4** as 
data.

#### Verifying a License for a user

Given an ISCC content identifier:

- Ask the user to sign a random nonce with his Wallet-ID
- Lookup the `smartlicense_attestation` stream for SmartLicenses attested to 
the user
- ...

### On-Chain Payment
...

## Validation

The first time given UUID4 is published to the stream as an item-key it is 
considered to be owned by the publishing Wallet-ID(s). Subsequent stream
entries with the same UUID4 key must be ignored if they are signed by a 
different Wallet-ID.
