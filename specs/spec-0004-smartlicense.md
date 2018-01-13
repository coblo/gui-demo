---
Spec: 4
Title: Smart Licenses
Author: Titusz <tp@py7.de>
Status: Draft
Created: 2018-01-12
License: BSD-2-Clause
---

# Smart Licenses

## Purpose

Allow content owners to manage content lincenses. This document specifies an 
open stream named `smartlicense` that can be used to publish machine readable
license information and contracting rules.

## Schema

The smartlicense-stream is readable and writable by every blockchain 
participant. An SmartLicense is identified by a publisher provided 
UUID Version 4.


## Validation

The first time given UUID4 is published to the stream as an item-key it is 
considered to be owned by the publishing Wallet-ID(s). Subsequent stream
entries with the same UUID4 key must be ignored if they are signed by a 
different Wallet-ID.
