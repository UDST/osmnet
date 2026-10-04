Unreleased
==========

* sends a User-Agent header with Overpass API requests and uses https, fixing HTTP 406 errors (#33, thanks to Rhys Williams)
* uses a descriptive User-Agent, ``osmnet/<version> (+https://github.com/UDST/osmnet)``, for both the interpreter and status requests
* ``get_pause_duration()`` now queries the status page over https with the User-Agent and finds the slot line by content, so it tolerates the current page layout
* retries are bounded: ``overpass_request()`` gets a ``max_retries`` argument (default 5) and raises ``OverpassRetryError`` when 429/504 responses persist; ``get_pause_duration()`` gets a ``max_retries`` argument and falls back to ``default_duration`` while the server stays busy
* adds a GitHub Actions workflow running the offline unit tests on Python 3.10-3.13

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

