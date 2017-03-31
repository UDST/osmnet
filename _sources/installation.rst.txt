Installation
=====================

OSMnet relies on a number of libraries in the scientific Python stack which can be easily installed using the `Anaconda`_ python distribution.

Dependencies
~~~~~~~~~~~~~~~~~~

* requests >= 2.9.1
* pandas >= 0.16.0
* numpy >= 1.10
* geopandas >= 0.2.1
* Shapely >= 1.5

Current status
~~~~~~~~~~~~~~~~~~

*Forthcoming improvements:*

* Tutorial/demo

Installation
~~~~~~~~~~~~~~~~~~

conda
^^^^^^^^^^^^^

conda installation is forthcoming.

pip
^^^^^^^^^^^^^

OSMnet can be installed via PyPI:

``pip install osmnet``

Development Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^

To install use the ``develop`` command rather than ``install``. Make sure you
are using the latest version of the code base by using git’s ``git pull``
inside the cloned repository.

To install OSMnet follow these steps:

1. Git clone the `OSMnet repo`_
2. in the cloned directory run: ``python setup.py develop``

To update to the latest version:

Use ``git pull`` inside the cloned repository


.. _Anaconda: http://docs.continuum.io/anaconda/
.. _OSMnet repo: https://github.com/udst/osmnet