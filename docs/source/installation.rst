Installation
============

OSMnet is built on top of the Python data science stack, making use of libraries like NumPy and Pandas, plus geospatial packages such as GeoPandas and Shapely.

OSMnet requires Python 3.10 or later.


Conda
^^^^^

OSMnet is distributed on Conda Forge and can be installed with:

``conda install osmnet --channel conda-forge``

OSMnet itself is pure Python code (no compilation needed), and its geospatial dependencies are distributed as pre-built packages on Conda Forge.


Pip
^^^

OSMnet is also distributed on PyPI:

``pip install osmnet``

If you run into errors related to dependency installation, try (a) setting up a clean environment and installing again, or (b) using Conda instead of Pip.


Installing from source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can install a development version of OSMnet by cloning the GitHub repository (or a fork or branch) and running this:

``pip install -e .``
