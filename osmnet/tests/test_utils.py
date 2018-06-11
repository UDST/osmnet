import numpy.testing as npt
import logging as lg

from osmnet.utils import great_circle_dist as gcd, log


def test_gcd():
    # tested against geopy
    # https://geopy.readthedocs.org/en/latest/#module-geopy.distance
    lat1 = 41.49008
    lon1 = -71.312796
    lat2 = 41.499498
    lon2 = -81.695391

    expected = 864456.76162966

    npt.assert_allclose(gcd(lat1, lon1, lat2, lon2), expected)


def test_logging():
    log('test debug message', level=lg.DEBUG)
    log('test info message', level=lg.INFO)
    log('test warning message', level=lg.WARNING)
    log('test error message', level=lg.ERROR)
