# Construct Additional Obelisks

After years of copy-pasting and modifying Obelisk client implementations all over,
we've had enough of hearing "construct additional obelisks".
Thus, we have decided to build the one client to rule them all.

## Usage

Take your pick of asynchronous or sync,
import the relevant Producer or Consumer and go crazy.
There is explicitly minimal documentation on actual filter values,
read the [Obelisk docs](https://obelisk.docs.apiary.io/) for that.

Please never copy the repo into your own project,
rather use `pip install construct-addditional-obelisks`.

## Retry strategies

Construct Additional Obelisks provides first class support for retry behaviours.
These are defined in `strategies/retry.py`,
we provide `NoRetryStrategy`, `ImmediateRetryStrategy`, 
and `ExponentialBackoffRetryStrategy.`
These do exactly what it says on the tin,
when provided in the constructor of your producer, consumer or client,
they will cause the client to retry requests according to the strategy
whenever the response status is not in the 2XX range.

The default strategy is no retry,
we do recommend setting at least some form of retry
as the token validity behaviour sometimes encounters edge cases.

## Async and Sync support

The library has an async and blocking edition.
The async edition is contained in the module `asynchronous` 
due to `async` being a reserved keyword and invalid package name,
synchronous can be found in `sync`. 
The `sync` edition is simply a wrapper around `asynchronous`, 
maintaining an own event loop.

## HFS and Classic support

All constructors take an optional `kind` argument,
set this to the appropriate variety for you.

There is no special handling for HFS userId / patientId fields as those are never
directly touched by the library.
The only exception is that `Datapoint` has explicit support for userId
and allows extra fields to provide naive support for other field names.

## Credits

Base implementation originally by Pieter Moens <Pieter.Moens@ugent.be>,
modified by Kyana Bosschaerts <Kyana.Bosschaerts@ugent.be>
and finally consolidated by Stef Pletinck <Stef.Pletinck@ugent.be>.
