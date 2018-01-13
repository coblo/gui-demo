---
Spec: 3
Title: ISCC Registration
Author: Titusz <tp@py7.de>
Status: Draft
Created: 2018-01-13
License: BSD-2-Clause
---

# ISCC

## Purpose

Registration off (ISCC)[http://iscc.codes/] content identifiers.


The ISCC-stream is readable and writable by every blockchain participant.
Stream-keys must be fully qualified **ISCC**s , formatted as 
`MetaID`-`ContentID`-`DataID`-`InstanceID`. The data_hex value has to be a 
hex encoded json, formatted as:

    {
        "title": "my_title",
        "extra": "my_extra"
    }
