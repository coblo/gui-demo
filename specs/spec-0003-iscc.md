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

An open an public registry for (ISCC)[http://iscc.codes/] content identifiers. This documents specifies an open stream named `iscc` that can be used to register ISCC content codes and their associated metadata.

## Schema

The ISCC-stream is named `iscc` and is readable and writable by every blockchain participant. The stream uses multiple keys for each stream-item where each key represents one of the 4 ISCC components:
`MetaID`, `ContentID`, `DataID`,`InstanceID`.

The stream-item value must be a json object that supports the following fields:

### title (required)

Title of an intangible creation.

The UTF-8 encoded value of the `title`-field must not exceed 128 bytes. For a valid **ISCC** entry the value of this field together with the optional `extra`-field must encode to the MetaID that was given as the first key of the stream-item.

### extra (optional)

A short statement that distinguishes this intangible creation from another one. 

The UTF-8 encoded value of the `extra`-field must not exceed 128 bytes.

### metadata (optional)

A list of one or more metadata entries. Must include at least one entry if specified. 

A metadata entry allows for a flexible and extendable way to supply additional media- type or industry specific metadata about the identified content. It is a JSON object with the fields `schema`, `encoding`, `data`, `url`. The `schema`-field is required and indicates the metadata schema (such as Dublin Core, IPTC, ID3v2, ONIX) that is used. The `encoding`-field is required if the indicated `schema` allows for different encoding formats (XML, JSON, BINARY ...). The `data`-field is only required if the`url` field is omitted. It holds the base64 encoded metadata conforming to the indicated schema. The `url`-field is only required if the `data`-field is omitted. The url is an external link that is expected tho host the metadata with the indicated schema.  

### tails (optional)

Extended ISCC-Component data.

A JSON object with the following possible fields `meta`, `content`, `data`, `instance`, where the values are 192-bit hex encoded ISCC component tails. At least one of the listed fields is required for a valid tails JSON object. Notes: ISCC components are assembled from a 1-byte header and an 8-byte main section. The main section is the truncated version of a 32-byte fingerprint. This field allows to supply the remaining 24-byte extended component data for advanced use cases that require higher dimensional binary vectors.

    {
        "title": "my_title",
        "extra": "my_extra"
    }
