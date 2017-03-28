# OSMnet
[![Build Status](https://travis-ci.org/UDST/osmnet.svg?branch=master)](https://travis-ci.org/UDST/osmnet)

Tools for the extraction of OpenStreetMap (OSM) street network data. Intended to be used in tandem with Pandana and UrbanAccess libraries to extract street network nodes and edges.

# Overview
OSMnet offers tools to download street network data from OpenStreetMap and extract a graph network comprised of nodes and edges to be used in [Pandana](https://github.com/UDST/pandana) street network accessibility calculations. 

# Library Status
OSMnet is currently in a alpha release. Forthcoming improvements:
- Tutorial/demo

## Reporting bugs
Please report any bugs you encounter via [GitHub issues](https://github.com/UDST/osmnet/issues).

## Contributing to OSMnet
If you have improvements or new features you would like to see in OSMnet:
1. Open a feature request via [GitHub issues](https://github.com/UDST/osmnet/issues).
2. Contribute your code from a fork or branch by using a Pull Request and request a review so it can be considered as an addition to the codebase.

## Installation
pip and conda installations are forthcoming. OSMnet is currently in a alpha release. As such, it is suggest to install using the ``develop`` command rather than ``install``. Make sure you are using the latest version of the code base by using git's ``git pull`` inside the cloned repository.

To install OSMnet follow these steps:

1. Git clone the [OSMnet repo](https://github.com/udst/osmnet)
2. in the cloned directory run: ``python setup.py develop``

To update to the latest version:

Use ``git pull`` inside the cloned repository

## Documentation

Documentation for OSMnet can be found [here](https://udst.github.io/osmnet/index.html).

# Related UDST libraries
- [Pandana](https://github.com/UDST/pandana)
- [UrbanAccess](https://github.com/UDST/urbanaccess)