---
Spec: 2
Title: Content Timestamping
Author: Titusz <tp@py7.de>
Status: Draft
Created: 2017-11-09
License: BSD-2-Clause
---

# Content Timestamping

## Purpose

Content Timestamping is used to record a digital fingerprint of a document on 
decentralized and tamper-proof blockchain. The timestamp serves as a secure 
proof of the time at which that document existed. It also secures the
integrity of the timestamped data without publicly revealing the content
itself. Additionaly publisher of a timespamping transaction can prove control
over the address that signed the transaction. This document speciefies an
open timestamping stream named `timestamp` that can be used to publish
document of file hashes as proof of existence.

## Schema

The timestamp-stream is readable and writable by every blockchain participant.
The timestamp key must be published as a hex encoded sha256 hash of the data
to be timestamped. The data_hex value is optional.

If data_hex is included it must be a (UBJSON)[http://ubjson.org/]-encoded
data-mapping. Currently the only officially recognized key in that 
datamapping is `comment` which can be any comment about the timestamped 
document like document name, version or reason for timestamping. 
The maximum processed length of `comment` is 280 characters.
