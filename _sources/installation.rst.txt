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

Note for Windows Users when Installing Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are a Windows user and you find when importing osmnet you see an error like this: ``ImportError: DLL load failed: The specified module could not be found.`` Most likely one of osmnet's dependencies did not install or compile correctly on your Windows machine. ``geopandas`` requires the dependency package ``fiona`` which requires the dependency package ``gdal``. Windows users should not install these dependencies via conda or pip, instead you should download and install these packages via `Christoph Gohlke Windows python wheels`_: `GDAL Windows Wheel`_ and `Fiona Windows Wheel`_. Download the package that matches your Python version and Windows system architecture, then cd into the download directory and install each package for example using: ``pip install Fiona-1.7.6-cp27-cp27m-win_amd64.whl`` and
``pip install GDAL-2.1.3-cp27-cp27m-win_amd64.whl``
If you have already installed these packaged via conda or pip, force a reinstall: ``pip install Fiona-1.7.6-cp27-cp27m-win_amd64.whl --upgrade --force-reinstall`` and
``pip install GDAL-2.1.3-cp27-cp27m-win_amd64.whl --upgrade --force-reinstall``

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
are using the latest version of the codebase by using git’s ``git pull``
inside the cloned repository.

To install OSMnet follow these steps:

1. Git clone the `OSMnet repo`_
2. in the cloned directory run: ``python setup.py develop`` or without dependencies: ``python setup.py develop --no-deps``

To update to the latest version:

Use ``git pull`` inside the cloned repository


.. _Anaconda: http://docs.continuum.io/anaconda/
.. _OSMnet repo: https://github.com/udst/osmnet
.. _Christoph Gohlke Windows python wheels: http://www.lfd.uci.edu/~gohlke/pythonlibs/
.. _GDAL Windows Wheel: http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
.. _Fiona Windows Wheel: http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona