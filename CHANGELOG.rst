Version 2.0.6
-------------

:Date: November 24, 2025

* Fix: Limit is now strict on multi-page queries in CORE

Version 2.0.5
-------------

:Date: November 21, 2025

* Fix: For small total limits, core.Client.query would return too many results

Version 2.0.4
-------------

:Date: October 29, 2025

* Fix: groupBy, orderBy and fields in Core are passed as repeating query parameter, rather than comma-separated string

Version 2.0.3
-------------

:Date: October 10, 2025

* Fix: Overridden constructor in `core.Client` does not pass `self`

Version 2.0.2
-------------

:Date: October 10, 2025

* Fix: Remove kind parameter from CORE client, see #13 and #12

Version 2.0.1
-------------

:Date: October 9, 2025

* Fix: CORE `query` now bails when less data is available than requested

Version 2.0.0
-------------

:Date: September 11, 2025

* Move split Consumer and Producer implementations into joint Client
* Implement Obelisk CORE in async mode.
* Token and token expiry are now private fields of BaseClient

Version 1.0.0
-------------

:Date: March 12, 2025

* Switch to new Construct Additional Obelisks implementation

Version 0.2.0
-------------

:Date: November 16, 2022

* Updated to Obelisk v3 stable deployment

Version 0.1.1
-------------

:Date: December 22, 2021

* Updated streaming using the `sqglc` package
* Updated example usage
* Updated documentation

Version 0.1.0
-------------

:Date: December 14, 2021

* Support for Obelisk v3
* PyPI package released

Version 0.0.6
-------------

:Date: November 3, 2020

* Switched from sseclient to sseclient-py for Server-Sent Events which supports larger payloads


Version 0.0.5
-------------

:Date: September 8, 2020

* Bugfix in consumer logic

Version 0.0.4
-------------

:Date: September 7, 2020

* Support for Python 3.6

Version 0.0.3
-------------

:Date: July 9, 2020

* Renamed package
* Removed support for multiple API versions
* Added methods for metadata endpoints

Version 0.0.2
-------------

:Date: June 15, 2020

* Simplified authentication flow

Version 0.0.1
-------------

:Date: June 15, 2020
