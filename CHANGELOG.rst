Unreleased
==========

* sends a User-Agent header with Overpass API requests and uses https, fixing HTTP 406 errors (#33, thanks to Rhys Williams)
* uses a descriptive User-Agent, ``osmnet/<version> (+https://github.com/UDST/osmnet)``, for both the interpreter and status requests
* ``get_pause_duration()`` now queries the status page over https with the User-Agent and finds the slot line by content, so it tolerates the current page layout
* retries are bounded: ``overpass_request()`` gets a ``max_retries`` argument (default 5) and raises ``OverpassRetryError`` when 429/504 responses persist; ``get_pause_duration()`` gets a ``max_retries`` argument and falls back to ``default_duration`` while the server stays busy
* unless ``error_pause_duration`` is given, retries wait at least 5 seconds, doubling up to 60, even when the status page reports free slots, so 504s from an overloaded server are not retried back to back
* ``osm_net_download()``, ``ways_in_bbox()`` and ``network_from_bbox()`` accept ``max_retries`` and pass it on to each Overpass request, so large downloads can allow more retries
* the wait for the next free slot is read from the status page's "in N seconds" rather than computed from its timestamp and the local clock; ``python-dateutil`` is no longer imported
* the interpreter request goes to ``overpass-api.de``, the same host as the status request
* server remarks in an Overpass response are logged as warnings, as intended
* requires Python 3.10 or later; tested on Python 3.10-3.14 with NumPy 2, pandas 3 and GeoPandas 1.x, and with the new minimum versions NumPy 1.21, pandas 1.5, GeoPandas 0.11, Shapely 1.8 and requests 2.28
* packaging moves from ``setup.py`` to ``pyproject.toml``, with ``test``, ``docs`` and ``dev`` extras; the license is declared as ``AGPL-3.0-only``
* no longer uses GeoPandas' deprecated ``GeoSeries.unary_union``
* the tests replay saved Overpass API responses, so they no longer depend on the live API or on later edits to OpenStreetMap; ``OSMNET_RECORD_OVERPASS=1`` refreshes the saved responses, and the live API tests in ``test_live.py`` run with ``OSMNET_LIVE_TESTS=1``
* CI on GitHub Actions: minimum dependencies on Python 3.10, latest dependencies on Python 3.14 (Linux, macOS, Windows), code style, package build and install, and a strict documentation build; Travis and AppVeyor configurations removed
* releases are published to PyPI by a GitHub Actions workflow using Trusted Publishing, after the distributions are built and the tests pass against the installed wheel; ``CONTRIBUTING.md`` describes the release process

v0.1.7
======

2023/8/7

* adds support for Shapely 2.0

v0.1.6
======

2020/7/13

* adds support for GeoPandas v0.7 and later
* ends support for Python 2.7 and Win32

v0.1.5
======

2018/6/15

* adds custom_osm_filter parameter
* update default keep_osm_tags list to include more tags including area
* add new exceptions to catch for queries that return bad/no data
* add coveralls support

v0.1.4
======

2017/4/6

* Better exception handling of KeyError exceptions.
* Removed unnecessary logs.

v0.1.3
======

2017/4/6

* Documentation is now generated and upload to the gh-pages branch after each commit on master.

v0.1.2
======

2017/3/31

* Now version numbers are the same in all the source code.

v0.1.1
======

2017/3/31

* README file changed from MarkDown to RST format.

v0.1.0
======

2017/3/31

* Python3 support. Now, Travis run tests over Python2.7 and Python3.5.
* Travis runs pycodestyle on each commit.
* Code now conforms pep8 and pycodestyle.

