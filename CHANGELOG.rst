=========
Changelog
=========

Unreleased
==========

Version 2.1.5
=============
- Upgrade pyscaffold to 3.3.1

Version 2.1.4
=============
- Remove Travis-ci from project
- Fix hectare unit scale in roi representation
- Fix documentation example for get_value with lat keyword
- Add 3 retries to get_roi_df method before raising an error

Version 2.1.3
=============
- Import warnings module

Version 2.1.2
=============
- Added `provide_coverage` keyword to synchronous roi time series request
- Fix bug when filtering rois on decsription regex when descriptions were missing
- Add deprecation warning for `delete_rois_from_account` to be be replaced with an roi.delete()

Version 2.1.1
=============
- Added `provide_coverage` keyword to roi-time series and --provide-coverage, -cov to cli

Version 2.1.0
=============
- Roi options expanded in python api: filter, update, hide-all, show-all
- Use unambiguous date and time formats in logs
- fix cli user info command

----

Version 2.0.4
=============
- Add --backward to cli
- fix CLI

Version 2.0.3
=============
- Bugfix: Delete method supplied with incorrect authentication

Version 2.0.2
=============
- Re-introduce tests for CI
- Explicit documentation for parallel point time-series
- Refactor for Requester object shared accross modules

Version 2.0.1
=============
- Add option backward average on time-series
- Set debug level in init as integer between 0-50

Version 2.0.0
=============

Major overhaull on the package API. basic functionalities remain the same.
The most important changes:

- Documentation update
- Dropped support for Python 2.7
- Removed all api/v1 endpoints from the codebase
- Refractored the command line from `$ vds api` to `$ vds-api`
- Removed unnecessary properties
- Retrieve DataFrames using the `roi-time-series-sync` endpoint
- VdsApiV2 class was simplified to 3 steps
- VdsApiV2 methods reflect their functionality

Refer to the documentation for the current syntax

----

Version 1.0.4
=============

Added features
- request from `staging` and `test` hosts aside from `maps`
- impersonating an account can also be done using the api client

Removed features
- dropped python 2.7 tests

Version 1.0.3
=============

Added features
- Filter ROIS based on id, name, area or description
- Deletion of a list of ROIS

Version 1.0.2
=============

Much change in this new version

Some added features:

- time-series returned as DataFrame
- roi request by name
- submit v2 jobs simultaneously
- get point value endpoint added in python api

and some stability enhancements:

- joblib and retrying dependencies added for parallel jobs and exception handling
- retry status update if no response
- save uuids to textfile until download finished,
enables you to retry a request if the script failed in between
submission and retrieval of the request


Version 1.0.1
=============
This version includes some minor bugfixes and enhancements:

- fixed the cli login procedure
- login the api client using environment variables also in the python api
- fixed testing for new time-series file naming
- fixed cli info when no rois were added to the account
- __repr__ of api base now returns __str__
- Rois class now has a py2/3 compatible bool() method (empty / non-empty)


Version 1.0.0
=============
This version has some changes in the Python API

- VanderSat API v2 gridded data downloads
- VanderSat API v2 time-series downloads
- CLI overhaul, v1 commands still included
- Overall consistency and stability upgrade

----

Version 0.1.5
=============

- PEP8 improvements
- Refractor from one class to base, cli, v1, v2 and wms
- Simplified and more consistent
- Enhanced flexibility

bugfixes
--------
- negative latlon for filenames
- credentials parsing improved
- writing of tempfile for streamed time-series for linux systems

added features
--------------
- testing functions added for cli, base and v1 commands
- removed credentials from logging
- Python 3 compatibility added
- Linux and Windows supported
- added info command to cli
- added login and logout methods to cli
- get credentials from environment variables (cli)
- automated check for existing products during configure

------

Version 0.1.0
=============

- multithreading implemented
- auto retry implemented
- click implementation for command line requests
- test command added to cli
- remove pandas from requirements for date_range
- added pandas when using streamed time-series
- retry all calls that were rejected by the server
- set different server though self.base
- KeyboardInterrupt implementation fixed for multithreading
- overwrite files swith added
- debug switch implemented
- log everything
- implemented option for using stream
- added multiple products to getarea command
- added multiple dates to getarea commands
- summary of performed operations