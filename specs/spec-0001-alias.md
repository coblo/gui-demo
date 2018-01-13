---
Spec: 1
Title: Wallet Address Aliases
Author: Titusz <tp@py7.de>
Status: Draft
Created: 2017-10-31
License: BSD-2-Clause
---

# Wallet Address Aliases

## Purpose

Wallet addresses are hard to memorize. This document specifies an open alias
stream  named `alias` that can be used to register one human readable unique
alias per address.

## Schema

The alias-stream is readable and writable by every blockchain participant. An 
alias is registered as stream key in the alias-stream without any data. The 
wallet address of the alias is derived from the stream-item-publisher who 
signed the publishing transaction.

## Updating

A previously registered alias for an address can only be updated by the 
original registrant. This is done by publishing a new available alias as key 
to the alias-stream signed by the same publishers address. Updating an alias 
releases the old alias for registration by other wallet addresses.

## Re-Assigning

An alias can be re-assigned to a new address after the autoritative owner has 
released the alias by registering another alias to his address.


## Validation

The first occurence of an unregistered or previously released alias is to be 
treated as the authoritative entry.

A valid alias stream entry has to have:

- at least one confirmation
- exactly one publisher
- emtpy data-hex
- a key that is a a valid alias
- a key that is not already assigned to another publisher (Wallet-ID)

A valid alias must match the following regex:

    ^                  # beginning of string
    (?!_$)             # no only _
    (?![-.])           # no - or . at the beginning
    (?!.*[_.-]{2})     # no __ or _. or ._ or .. or -- inside
    [a-z0-9_.-]{3,30}  # allowed characters (between 3 and 30)
    (?<![.-])          # no - or . at the end
    $                  # end of string

All stream items that are not conforming to these rules must be ignored by the 
stream parsing application. If a publisher announces a new alias the old 
becomes available to be re-assigned. Applications must be aware of the fact 
that address-alias mappings may change over time.
