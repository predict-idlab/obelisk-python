# Construct Additional Obelisks

After years of copy-pasting and modifying Obelisk client implementations all over,
we've had enough of hearing "construct additional obelisks".
Thus, we have decided to build the one client to rule them all.

## Async and Sync support

The library has an async and blocking edition.
The async edition is contained in the module `asynchronous` due to `async` being a reserved keyword and invalid package name,
synchronous can be found in `sync`. 
The `sync` edition is simply a wrapper around `asynchronous`, maintaining an own event pool

## Credits

Base implementation originally by Pieter Moens <Pieter.Moens@ugent.be>,
modified by Kyana Bosschaerts <Kyana.Bosschaerts@ugent.be>
and finally consolidated by Stef Pletinck <Stef.Pletinck@ugent.be>.
