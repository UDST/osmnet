import os

import pytest

import osmnet.load as load

# These tests query the live Overpass API, so they are skipped unless
# OSMNET_LIVE_TESTS=1. The tests in test_load.py replay saved responses.
pytestmark = pytest.mark.skipif(
    os.environ.get('OSMNET_LIVE_TESTS') != '1',
    reason='queries the live Overpass API; set OSMNET_LIVE_TESTS=1 to run')


def test_get_pause_duration():
    pause = load.get_pause_duration(recursive_delay=5, default_duration=10)
    assert pause >= 0


def test_overpass_request_raises():
    # a query timeout of 0 makes the server return an error, not JSON
    query_str = ('[out:json][timeout:0];(way["highway"]'
                 '(37.80381120,-122.29655747,37.80564009,-122.29359631);'
                 '>;);out;')
    with pytest.raises(Exception):
        load.overpass_request(data={'data': query_str})


def test_network_from_bbox():
    nodes, edges = load.network_from_bbox(
        bbox=(-122.2965574674, 37.8038112007, -122.2935963086, 37.8056400922),
        custom_osm_filter='["highway"="service"]')
    assert len(nodes) > 0
    assert len(edges) > 0
    for col in ['x', 'y']:
        assert col in nodes.columns
    for col in ['distance', 'from', 'to']:
        assert col in edges.columns
