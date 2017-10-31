# Application Streams

This application depends on multiple streams being avaible on the blockchain:

## alias
The `alias` stream is open and used to register a human readable and easy to memorize
name for an address. Aliases are registered in the stream as keys. The alias for an address
can be updated by publishing a new key to the stream from the same publisher address.

A valid alias stream entry has to have:
- exactly one publisher
- empty data
- a key between 3 and 30 characters length
- a key that is not already assigned to another publisher

All stream items not conforming to these rules must be ignored.

If a publisher changes his alias his/her old alias becomes available
to be assigned to another address. Applications should be aware of the
fact that address-alias mappings might change over time.
