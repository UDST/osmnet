v0.2
====

2026/11/19

First release since v0.1.7 in August 2023. It restores downloads from the Overpass API, which fail with HTTP 406 errors in v0.1.7, bounds the retries when the server is busy, and updates the package for current versions of Python and the geospatial libraries.

* sends a descriptive User-Agent, ``osmnet/<version> (+https://github.com/UDST/osmnet)``, with requests to the Overpass API and uses https and the ``overpass-api.de`` host for both the interpreter and status endpoints, fixing the HTTP 406 errors (#33, #34)
* ``get_pause_duration()`` finds the slot information on the status page by content, so it tolerates the current page layout, and reads the wait from the page's "in N seconds" rather than computing it from a timestamp and the local clock; ``python-dateutil`` is no longer imported (#34)
* retries are bounded: ``overpass_request()`` gets a ``max_retries`` argument (default 5) and raises the new ``OverpassRetryError``, which includes the server's last response, when 429, 502, 503 or 504 responses persist. ``osm_net_download()``, ``ways_in_bbox()`` and ``network_from_bbox()`` accept ``max_retries`` and pass it on to each request, so large downloads can allow more retries (#34, #38)
* 502 and 503 responses are retried like 429 and 504; the public Overpass server now answers 502 when it is at capacity (#38)
* unless ``error_pause_duration`` is given, retries wait at least 5 seconds, doubling up to 60, so requests to an overloaded server are not retried back to back; after a 429 the wait is the status page's wait for the next free slot if that is longer (#34, #38)
* ``get_pause_duration()`` gets a ``max_retries`` argument and falls back to ``default_duration`` while the server stays busy (#34)
* server remarks in an Overpass response are logged as warnings, as intended (#34)
* requires Python 3.10 or later; tested on Python 3.10-3.15 with NumPy 2, pandas 3 and GeoPandas 1.x, and with the new minimum versions NumPy 1.21, pandas 1.5, GeoPandas 0.11, Shapely 1.8 and requests 2.28 (#35, #38)
* no longer uses GeoPandas' deprecated ``GeoSeries.unary_union`` or the ``inplace`` keyword that pandas 3.1 deprecates (#35, #38)
* packaging moves from ``setup.py`` to ``pyproject.toml``, with ``test``, ``docs`` and ``dev`` extras; the license is declared as ``AGPL-3.0-only`` (#35)
* the tests replay saved Overpass API responses, so they no longer depend on the live API or on later edits to OpenStreetMap (#35)
* GitHub Actions replaces Travis and AppVeyor: CI tests the minimum dependencies on Python 3.10 and the latest dependencies on Python 3.15 (Linux, macOS, Windows), and checks code style, the package build and the documentation build (#34, #35, #38). Releases are published to PyPI by a workflow using Trusted Publishing (#38)
* the README describes the project's scope and status (#32)
* ``main`` is now the integration branch; ``dev`` is retired
* thanks to Rhys Williams for the User-Agent fix and to Paul Waddell for the status check, retry and CI work

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

