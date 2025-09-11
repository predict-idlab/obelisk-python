# Obelisk-Python

After years of copy-pasting and modifying Obelisk client implementations all over,
we've had enough of hearing "construct additional obelisks".
Thus, we have decided to build the one client to rule them all.

This project is licensed according to the LICENSE file included with the source.
You should have received a copy alongside the code bundle,
otherwise you can get it for the most recent version [here](https://github.com/predict-idlab/obelisk-python/blob/main/LICENSE).

## Usage

Take your pick of asynchronous or sync,
import the relevant Producer or Consumer and go crazy.
There is explicitly minimal documentation on actual filter values,
read the [Obelisk docs](https://obelisk.docs.apiary.io/) for that.
Documentation for the Python API can be found [here](https://predict-idlab.github.io/obelisk-python/).

Please never copy the repo into your own project,
rather use `pip install obelisk-py`.

### Retry strategies

Obelisk-py provides first class support for retry behaviours.
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

### Async and Sync support

The library has an async and blocking edition.
The async edition is contained in the module `asynchronous` 
due to `async` being a reserved keyword and invalid package name,
synchronous can be found in `sync`. 
The `sync` edition is simply a wrapper around `asynchronous`, 
maintaining an own event loop.

### HFS and Classic support

All constructors take an optional `kind` argument,
set this to the appropriate variety for you.

There is no special handling for HFS userId / patientId fields as those are never
directly touched by the library.
The only exception is that `Datapoint` has explicit support for userId
and allows extra fields to provide naive support for other field names.

## Building and Docs

`uv` is used to manage this project.
Tests can be run using `uv run pytest`, building and deployment are handled by `uv build` and `uv publish`.

Documentation uses the classic `sphinx` setup, with numpydoc for their lovely layouts and conventions.
Building is as follows:

``` sh
# uv run sphinx-build -M html docs/source/ docs/build/
```

In case of major restructuring, it may be needed to clean up the contents of `docs/_autosummary` and potentially other rst files in `docs`,
followed by re-running the build.
Manually triggering sphinx-apidoc is unnecessary.

## Credits

Base implementation originally by Pieter Moens <Pieter.Moens@ugent.be>,
modified by Kyana Bosschaerts <Kyana.Bosschaerts@ugent.be>
and finally consolidated by Stef Pletinck <Stef.Pletinck@ugent.be>.

