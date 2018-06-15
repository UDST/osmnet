import numpy.testing as npt
import pandas.util.testing as pdt
import pytest
import shapely.geometry as geometry

import osmnet.load as load


@pytest.fixture(scope='module')
def bbox1():
    # Intersection of Telegraph and Haste in Berkeley
    # Sample query: http://overpass-turbo.eu/s/6AK
    return 37.8659303546, -122.2588003879, 37.8661598571, -122.2585062512


@pytest.fixture(scope='module')
def bbox2():
    # Telegraph Channing to Durant in Berkeley
    # Sample query: http://overpass-turbo.eu/s/6B0
    return 37.8668405874, -122.2590948685, 37.8679028054, -122.2586363885


@pytest.fixture(scope='module')
def bbox3():
    # West Berkeley including highway 80, frontage roads, and foot paths
    # Sample query: http://overpass-turbo.eu/s/6VE
    return (
        37.85225504880375, -122.30295896530151,
        37.85776128099243, - 122.2954273223877)


@pytest.fixture
def bbox4():
    return (-122.2762870789, 37.8211879615,
            -122.2701716423, 37.8241329692)


@pytest.fixture
def bbox5():
    return (-122.2965574674, 37.8038112007,
            -122.2935963086, 37.8056400922)


@pytest.fixture
def simple_polygon():
    polygon = geometry.Polygon([[0, 0], [1, 0], [1, 1], [0, 1]])
    return polygon


@pytest.fixture(scope='module')
def query_data1(bbox1):
    lat_min, lng_max, lat_max, lng_min = bbox1
    query_template = '[out:json][timeout:{timeout}]{maxsize};(way["highway"]' \
                     '{filters}({lat_min:.8f},{lng_max:.8f},{lat_max:.8f},' \
                     '{lng_min:.8f});>;);out;'
    query_str = query_template.format(lat_max=lat_max, lat_min=lat_min,
                                      lng_min=lng_min, lng_max=lng_max,
                                      filters=load.osm_filter('walk'),
                                      timeout=180, maxsize='')
    return load.overpass_request(data={'data': query_str})


@pytest.fixture(scope='module')
def query_data2(bbox2):
    lat_min, lng_max, lat_max, lng_min = bbox2
    query_template = '[out:json][timeout:{timeout}]{maxsize};(way["highway"]' \
                     '{filters}({lat_min:.8f},{lng_max:.8f},{lat_max:.8f},' \
                     '{lng_min:.8f});>;);out;'
    query_str = query_template.format(lat_max=lat_max, lat_min=lat_min,
                                      lng_min=lng_min, lng_max=lng_max,
                                      filters=load.osm_filter('walk'),
                                      timeout=180, maxsize='')
    return load.overpass_request(data={'data': query_str})


@pytest.fixture(scope='module')
def dataframes1(query_data1):
    return load.parse_network_osm_query(query_data1)


@pytest.fixture(scope='module')
def dataframes2(query_data2):
    return load.parse_network_osm_query(query_data2)


def test_make_osm_query(query_data1):
    assert isinstance(query_data1, dict)
    assert len(query_data1['elements']) == 26
    assert len([e for e in query_data1['elements']
                if e['type'] == 'node']) == 22
    assert len([e for e in query_data1['elements']
                if e['type'] == 'way']) == 4


def test_process_node():
    test_node = {
        'id': 'id',
        'lat': 'lat',
        'lon': 'lon',
        'extra': 'extra'
    }

    expected = {
        'id': 'id',
        'lat': 'lat',
        'lon': 'lon'
    }

    assert load.process_node(test_node) == expected

    test_node['tags'] = {'highway': 'highway', 'source': 'source'}
    expected['highway'] = 'highway'

    assert load.process_node(test_node) == expected


def test_process_way():
    test_way = {
        "type": "way",
        "id": 188434143,
        "timestamp": "2014-01-04T22:18:14Z",
        "version": 2,
        "changeset": 19814115,
        "user": "dchiles",
        "uid": 153669,
        "nodes": [
            53020977,
            53041093,
        ],
        "tags": {
            'source': 'source',
            "addr:city": "Berkeley",
            "highway": "secondary",
            "name": "Telegraph Avenue",
        }
    }

    expected_way = {
        'id': test_way['id'],
        'highway': test_way['tags']['highway'],
        'name': test_way['tags']['name']
    }

    expected_waynodes = [
        {'way_id': test_way['id'], 'node_id': test_way['nodes'][0]},
        {'way_id': test_way['id'], 'node_id': test_way['nodes'][1]}
    ]

    way, waynodes = load.process_way(test_way)

    assert way == expected_way
    assert waynodes == expected_waynodes


def test_parse_network_osm_query(dataframes1):
    nodes, ways, waynodes = dataframes1

    assert len(nodes) == 22
    assert len(ways) == 4
    assert len(waynodes.index.unique()) == 4


def test_parse_network_osm_query_raises():
    query_template = '[out:json][timeout:{timeout}]{maxsize};(way["highway"]' \
                     '{filters}({lat_min:.8f},{lng_max:.8f},{lat_max:.8f},' \
                     '{lng_min:.8f});>;);out;'
    query_str = query_template.format(lat_max=37.8, lng_min=-122.252,
                                      lat_min=37.8, lng_max=-122.252,
                                      filters=load.osm_filter('walk'),
                                      timeout=180, maxsize='')
    data = load.overpass_request(data={'data': query_str})
    with pytest.raises(RuntimeError):
        load.parse_network_osm_query(data)


def test_overpass_request_raises(bbox5):
    lat_min, lng_max, lat_max, lng_min = bbox5
    query_template = '[out:json][timeout:{timeout}]{maxsize};(way["highway"]' \
                     '{filters}({lat_min:.8f},{lng_max:.8f},{lat_max:.8f},' \
                     '{lng_min:.8f});>;);out;'
    query_str = query_template.format(lat_max=lat_max, lat_min=lat_min,
                                      lng_min=lng_min, lng_max=lng_max,
                                      filters=load.osm_filter('walk'),
                                      timeout=0, maxsize='')
    with pytest.raises(Exception):
        load.overpass_request(data={'data': query_str})


def test_get_pause_duration():
    error_pause_duration = load.get_pause_duration(recursive_delay=5,
                                                   default_duration=10)
    assert error_pause_duration >= 0


def test_quadrat_cut_geometry(simple_polygon):
    multipolygon = load.quadrat_cut_geometry(geometry=simple_polygon,
                                             quadrat_width=0.5,
                                             min_num=3,
                                             buffer_amount=1e-9)

    assert isinstance(multipolygon, geometry.MultiPolygon)
    assert len(multipolygon) == 4


def test_ways_in_bbox(bbox1, dataframes1):
    lat_min, lng_max, lat_max, lng_min = bbox1
    nodes, ways, waynodes = load.ways_in_bbox(lat_min=lat_min, lng_min=lng_min,
                                              lat_max=lat_max, lng_max=lng_max,
                                              network_type='walk')
    exp_nodes, exp_ways, exp_waynodes = dataframes1

    pdt.assert_frame_equal(nodes, exp_nodes)
    pdt.assert_frame_equal(ways, exp_ways)
    pdt.assert_frame_equal(waynodes, exp_waynodes)


@pytest.mark.parametrize(
    'network_type, noset',
    [('walk', {'motorway', 'motorway_link'}),
     ('drive', {'footway', 'cycleway'})])
def test_ways_in_bbox_walk_network(bbox3, network_type, noset):
    lat_min, lng_max, lat_max, lng_min = bbox3
    nodes, ways, waynodes = load.ways_in_bbox(lat_min=lat_min, lng_min=lng_min,
                                              lat_max=lat_max, lng_max=lng_max,
                                              network_type=network_type)

    for _, way in ways.iterrows():
        assert way['highway'] not in noset


def test_intersection_nodes1(dataframes1):
    _, _, waynodes = dataframes1
    intersections = load.intersection_nodes(waynodes)

    assert intersections == {53041093}


def test_intersection_nodes2(dataframes2):
    _, _, waynodes = dataframes2
    intersections = load.intersection_nodes(waynodes)

    assert intersections == {53099275, 53063555}


def test_node_pairs_two_way(dataframes2):
    nodes, ways, waynodes = dataframes2
    pairs = load.node_pairs(nodes, ways, waynodes)

    assert len(pairs) == 1

    fn = 53063555
    tn = 53099275

    pair = pairs.loc[(fn, tn)]

    assert pair.from_id == fn
    assert pair.to_id == tn
    npt.assert_allclose(pair.distance, 101.48279182499789)


def test_node_pairs_one_way(dataframes2):
    nodes, ways, waynodes = dataframes2
    pairs = load.node_pairs(nodes, ways, waynodes, two_way=False)

    assert len(pairs) == 2

    n1 = 53063555
    n2 = 53099275

    for p1, p2 in [(n1, n2), (n2, n1)]:
        pair = pairs.loc[(p1, p2)]

        assert pair.from_id == p1
        assert pair.to_id == p2
        npt.assert_allclose(pair.distance, 101.48279182499789)


def test_column_names(bbox4):

    nodes, edges = load.network_from_bbox(
        bbox=bbox4, network_type='walk', timeout=180, memory=None,
        max_query_area_size=50*1000*50*1000
    )
    col_list = ['x', 'y', 'id']
    for col in col_list:
        assert col in nodes.columns

    col_list = ['distance', 'from', 'to']
    for col in col_list:
        assert col in edges.columns


def test_custom_query_pass(bbox5):
    nodes, edges = load.network_from_bbox(
        bbox=bbox5, custom_osm_filter='["highway"="service"]'
    )
    assert len(nodes) == 22
    assert len(edges) == 30
    assert edges['highway'].unique() == 'service'
