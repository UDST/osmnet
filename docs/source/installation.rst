Installation
============

OSMnet is built on top of the Python data science stack, making use of libraries like NumPy and Pandas, plus geospatial packages such as GeoPandas and Shapely.

OSMnet v0.1.6 (July 2020) dropped support for Python 2.7 and 32-bit Windows environments. In these older environments, v0.1.5 should install automatically -- but if not, you can get it with ``conda install osmnet=0.1.5 ...`` or ``pip install osmnet==0.1.5``.


Conda
^^^^^

OSMnet is distributed on Conda Forge and can be installed with:

``conda install osmnet --channel conda-forge``

This is generally the smoothest installation route. Although OSMnet itself is pure Python code (no compilation needed), the geospatial dependencies often cause installation problems using the default Pip package manager, especially in Windows. You can obtain the Conda package manager by installing the `Anaconda <https://www.anaconda.com/products/individual#Downloads>`_ Python distribution.


Pip
^^^

OSMnet is also distributed on PyPI:

``pip install osmnet``

If you run into errors related to dependency installation, try (a) setting up a clean environment and installing again, or (b) using Conda instead of Pip.


Installing from source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can install a development version of OSMnet by cloning the GitHub repository (or a fork or branch) and running this:

``pip install -e .``


Windows troubleshooting
^^^^^^^^^^^^^^^^^^^^^^^

.. note::
   If you are a Windows user, dependency installation issues can be minimized by using Conda. However, if you find you are still having issues with dependencies -- such as when importing OSMnet you see an error like the one below -- most likely one of OSMnet's dependencies did not install or compile correctly on your machine. GeoPandas requires the dependency package Fiona, which in turn requires the dependency package GDAL. 
   
   .. code-block::
   
      ImportError: DLL load failed: The specified module could not be found
   
   You can try installing these dependencies via `Christoph Gohlke Windows python wheels`_: `GDAL Windows Wheel`_ and `Fiona Windows Wheel`_. Download the package that matches your Python version and Windows system architecture, then ``cd`` into the download directory and install each package like this, changing the file names as appropriate: 
   
   .. code-block::
   
      pip install Fiona-1.7.6-cp27-cp27m-win_amd64.whl
      pip install GDAL-2.1.3-cp27-cp27m-win_amd64.whl
      
   If you have already installed these via Conda or Pip, force a reinstall: 
   
   .. code-block::
   
      pip install Fiona-1.7.6-cp27-cp27m-win_amd64.whl --upgrade --force-reinstall
      pip install GDAL-2.1.3-cp27-cp27m-win_amd64.whl --upgrade --force-reinstall



.. _OSMnet repo: https://github.com/udst/osmnet
.. _Christoph Gohlke Windows python wheels: http://www.lfd.uci.edu/~gohlke/pythonlibs/
.. _GDAL Windows Wheel: http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
.. _Fiona Windows Wheel: http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona