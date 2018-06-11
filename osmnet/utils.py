# The following logging functions were modified from the osmnx library and
# used with permission from the author Geoff Boeing:
# log, get_logger: https://github.com/gboeing/osmnx/blob/master/osmnx/utils.py

from __future__ import division

import math
import logging as lg
import unicodedata
import sys
import datetime as dt
import os

from osmnet import config


def great_circle_dist(lat1, lon1, lat2, lon2):
    """
    Get the distance (in meters) between two lat/lon points
    via the Haversine formula.

    Parameters
    ----------
    lat1, lon1, lat2, lon2 : float
        Latitude and longitude in degrees.

    Returns
    -------
    dist : float
        Distance in meters.

    """
    radius = 6372795  # meters

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # formula from:
    # http://en.wikipedia.org/wiki/Haversine_formula#The_haversine_formula
    a = math.pow(math.sin(dlat / 2), 2)
    b = math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon / 2), 2)
    d = 2 * radius * math.asin(math.sqrt(a + b))

    return d


def log(message, level=None, name=None, filename=None):
    """
    Write a message to the log file and/or print to the console.

    Parameters
    ----------
    message : string
        the content of the message to log
    level : int
        one of the logger.level constants
    name : string
        name of the logger
    filename : string
        name of the log file

    Returns
    -------
    None
    """

    if level is None:
        level = lg.INFO
    if name is None:
        name = config.settings.log_name
    if filename is None:
        filename = config.settings.log_filename

    if config.settings.log_file:
        # get the current logger or create a new one then log message at
        # requested level
        logger = get_logger(level=level, name=name, filename=filename)
        if level == lg.DEBUG:
            logger.debug(message)
        elif level == lg.INFO:
            logger.info(message)
        elif level == lg.WARNING:
            logger.warning(message)
        elif level == lg.ERROR:
            logger.error(message)

    # if logging to console is turned on, convert message to ascii and print
    # to the console only
    if config.settings.log_console:  # pragma: no cover
        # capture current stdout, then switch it to the console, print the
        # message, then switch back to what had been the stdout
        # this prevents logging to notebook - instead, it goes to console
        standard_out = sys.stdout
        sys.stdout = sys.__stdout__

        # convert message to ascii for proper console display in windows
        # terminals
        message = unicodedata.normalize(
            'NFKD', str(message)).encode('ascii', errors='replace').decode()
        print(message)
        sys.stdout = standard_out
    # otherwise print out standard statement
    else:
        print(message)


def get_logger(level=None, name=None, filename=None):
    """
    Create a logger or return the current one if already instantiated.

    Parameters
    ----------
    level : int
        one of the logger.level constants
    name : string
        name of the logger
    filename : string
        name of the log file

    Returns
    -------
    logger : logger.logger
    """

    if level is None:
        level = config.settings.log_level
    if name is None:
        name = config.settings.log_name
    if filename is None:
        filename = config.settings.log_filename

    logger = lg.getLogger(name)

    # if a logger with this name is not already established
    if not getattr(logger, 'handler_set', None):

        todays_date = dt.datetime.today().strftime('%Y_%m_%d')
        log_filename = '{}/{}_{}.log'.format(config.settings.logs_folder,
                                             filename, todays_date)

        if not os.path.exists(config.settings.logs_folder):
            os.makedirs(config.settings.logs_folder)

        # create file handler and log formatter and establish settings
        handler = lg.FileHandler(log_filename, encoding='utf-8')
        formatter = lg.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.handler_set = True

    return logger
