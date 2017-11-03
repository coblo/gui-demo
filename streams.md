# Application Streams

This application depends on multiple streams being avaible on the blockchain:

## alias
The `alias` stream is open and used to register a human readable and easy to memorize
name for an address. Aliases are registered in the stream as keys without data.
The alias for an address can be updated by publishing a new key signed by the same
publisher address. The first occurence of an alias it the authoritative entry.
It can be re-assigned to a new address after the autoritative owner has
released it by registering another alias to his address.

A valid alias stream entry has to have:
- at least one confirmation
- exactly one publisher
- emtpy data-hex
- a key that is a a valid username
- a key that is not already assigned to another publisher

A valid username must match the following regex:

    ^                  # beginning of string
    (?!_$)             # no only _
    (?![-.])           # no - or . at the beginning
    (?!.*[_.-]{2})     # no __ or _. or ._ or .. or -- inside
    [a-z0-9_.-]{3,30}  # allowed characters (between 3 and 30)
    (?<![.-])          # no - or . at the end
    $                  # end of string

All stream items not conforming to these rules must be ignored.

If a publisher announces a new alias the old becomes available
to be re-assigned. Applications must be aware of the fact that
address-alias mappings change over time.
