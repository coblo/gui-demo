---
Spec: 3
Title: ISCC Registration v1.0
Author: Titusz <tp@py7.de>
Status: Draft
Created: 2018-01-13
License: BSD-2-Clause
---

# ISCC

## Purpose

An open an public registry for [ISCC](http://iscc.codes/) content identifiers. This documents specifies an open stream named `iscc` that can be used to register ISCC content codes and optionally associated metadata.

## Schema

The ISCC-stream is named `iscc` and is readable and writable by every blockchain participant. The stream uses multiple keys for each stream-item where each key represents one of the 4 ISCC components:
`MetaID`, `ContentID`, `DataID`,`InstanceID`.

The stream-item value must be a json object that supports a set of defined top-level fields which are specified below. Applications **may** add custom fields at the top level but **must** prefix those fields with an underscore to avoid collisions with future extensions of this specification. 

### Top-Level Fields

#### version (optional)

Version of ISCC registry schema. Assumed to be 1.0 if omitted.

#### title (required)

Title of an intangible creation.

The UTF-8 encoded value of the `title`-field must not exceed 128 bytes. For a valid **ISCC** entry the value of this field together with the optional `extra`-field must encode to the MetaID that was given as the first key of the stream-item.

#### extra (optional)

A short statement that distinguishes this intangible creation from another one. 

The UTF-8 encoded value of the `extra`-field must not exceed 128 bytes.

#### tails (optional)

Extended ISCC-Component data.

A JSON object with the following possible fields `meta`, `content`, `data`, `instance`, where the values are 192-bit hex encoded ISCC component tails. At least one of the listed fields is required for a valid tails JSON object. Notes: ISCC components are assembled from a 1-byte header and an 8-byte main section. The main section is the truncated version of a 32-byte fingerprint. This field allows to supply the remaining 24-byte extended component data for advanced use cases that require higher dimensional binary vectors.

#### metadata (optional)

A list of one or more metadata entries. Must include at least one entry if specified. 

A metadata entry allows for a flexible and extendable way to supply additional industry specific metadata about the identified content. It is a JSON object with the fields `schema`, `mediatype`, `data`, `url`. The `schema`-field may indicate a well known metadata schema (such as Dublin Core, IPTC, ID3v2, ONIX) that is used. The `mediatype`-field specifies an [IANA Media Type](https://www.iana.org/assignments/media-types/media-types.xhtml). The `data`-field is only required if the`url` field is omitted. It holds the metadata conforming to the indicated `schema` and `mediatype.` The `url`-field is only required if the `data`-field is omitted. The `url` is an external link that is expected to host the metadata with the indicated `schema` and `mediatype`.  

## Examples

Minimal **ISCC** registry entry value:

```json
{
  "title": "The Neverending Story"
}
```

With extra field:

```json
{
  "title": "The Neverending Story",
  "extra": "1984 fantasy film based on novel"
}
```

With extended **ISCC** tails:

```json
{
  "title": "The Neverending Story",
  "tails":
  {
    "meta": "6e5ef0c142805ffc66c721394a66236b57aba8f9aee000dd",
    "content": "5e3d5f623691d0e948cdc906f5c68602744934234fefdfa6",
    "data": "c0b07d2bbcc2c6fb97739c24c7a65964c042808c3885bcd3",
    "instance": "50859ea4550a2a27045c5c5dad39f8d198717486dc8fef79"
  }
}
```
With linked Metadata:

```json
{
  "title": "Ubu: A face-to-face connector app for Hubud members",
  "metadata": 
  [
    {
      "schema": "xmp",
      "mediatype": "application/rdf+xml",
      "url": "http://camwebb.info/blog/2014-11-19/ubu.xmp"
    }
  ]
}
```

With custom inline Metadata:

```json
{
  "title": "The Neverending Story",
  "metadata": 
  [{
    "schema": "schema.org",
    "mediatype": "application/ld+json",
    "data": 
      {
        "@context": "http://schema.org",
        "@type": "Movie",
        "name": "The Neverending Story",
        "dateCreated": "6 April, 1984",
        "director": "Wolfgang Petersen",
        "actors": ["Noah Hathaway", "Barret Oliver", "Tami Stronach"],
        "duration": "1:42:00"
      }
  }]
}
```

With application specific custom field:

```json
{
  "title": "The Neverending Story",
  "_productionCompany": "Bavaria Studios"
}
```
