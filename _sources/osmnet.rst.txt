Using OSMnet
============================================

Creating a graph network from a OSM street network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ``drive`` (e.g. automobile) or ``walk`` (e.g. pedestrian) graph network comprised of nodes and edges from OpenStreetMap (OSM) street network data via the OverpassAPI. Edges will be weighted by default by distance in units of meters. The resulting graph network is intended to be used with `Pandana`_ network accessibility queries and `UrbanAccess`_ to create an integrated transit and street graph network.

.. autofunction:: osmnet.load.network_from_bbox


.. _Pandana: https://github.com/UDST/pandana

.. _UrbanAccess: https://github.com/UDST/urbanaccess