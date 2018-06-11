# The following functions to download osm data, setup a recursive api request
# and subdivide bbox queries into smaller bboxes were modified from the
# osmnx library and used with permission from the author Geoff Boeing
# osm_net_download, overpass_request, get_pause_duration,
# consolidate_subdivide_geometry, quadrat_cut_geometry:
# https://github.com/gboeing/osmnx/blob/master/osmnx/core.py
# project_geometry, project_gdf:
# https://github.com/gboeing/osmnx/blob/master/osmnx/projection.py

from __future__ import division
from itertools import islice
import re
import pandas as pd
import requests
import math
import time
import logging as lg
import numpy as np
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import unary_union
from dateutil import parser as date_parser
import datetime as dt
import geopandas as gpd

from osmnet import config
from osmnet.utils import log, great_circle_dist as gcd


def osm_filter(network_type):
    """
    Create a filter to query Overpass API for the specified OSM network type.

    Parameters
    ----------
    network_type : string, {'walk', 'drive'} denoting the type of street
    network to extract

    Returns
    -------
    osm_filter : string
    """
    filters = {}

    # drive: select only roads that are drivable by normal 2 wheel drive
    # passenger vehicles both private and public
    # roads. Filter out un-drivable roads and service roads tagged as parking,
    # driveway, or emergency-access
    filters['drive'] = ('["highway"!~"cycleway|footway|path|pedestrian|steps'
                        '|track|proposed|construction|bridleway|abandoned'
                        '|platform|raceway|service"]'
                        '["motor_vehicle"!~"no"]["motorcar"!~"no"]'
                        '["service"!~"parking|parking_aisle|driveway'
                        '|emergency_access"]')

    # walk: select only roads and pathways that allow pedestrian access both
    # private and public pathways and roads.
    # Filter out limited access roadways and allow service roads
    filters['walk'] = ('["highway"!~"motor|proposed|construction|abandoned'
                       '|platform|raceway"]["foot"!~"no"]'
                       '["pedestrians"!~"no"]')

    if network_type in filters:
        osm_filter = filters[network_type]
    else:
        raise ValueError('unknown network_type "{}"'.format(network_type))

    return osm_filter


def osm_net_download(lat_min=None, lng_min=None, lat_max=None, lng_max=None,
                     network_type='walk', timeout=180, memory=None,
                     max_query_area_size=50*1000*50*1000,
                     custom_osm_filter=None):
    """
    Download OSM ways and nodes within a bounding box from the Overpass API.

    Parameters
    ----------
    lat_min : float
        southern latitude of bounding box
    lng_min : float
        eastern longitude of bounding box
    lat_max : float
        northern latitude of bounding box
    lng_max : float
        western longitude of bounding box
    network_type : string
        Specify the network type where value of 'walk' includes roadways
        where pedestrians are allowed and pedestrian
        pathways and 'drive' includes driveable roadways.
    timeout : int
        the timeout interval for requests and to pass to Overpass API
    memory : int
        server memory allocation size for the query, in bytes. If none,
        server will use its default allocation size
    max_query_area_size : float
        max area for any part of the geometry, in the units the geometry is
        in: any polygon bigger will get divided up for multiple queries to
        Overpass API (default is 50,000 * 50,000 units (ie, 50km x 50km in
        area, if units are meters))
    custom_osm_filter : string, optional
        specify custom arguments for the way["highway"] query to OSM. Must
        follow Overpass API schema. For
        example to request highway ways that are service roads use:
        '["highway"="service"]'

    Returns
    -------
    response_json : dict
    """

    # create a filter to exclude certain kinds of ways based on the requested
    # network_type
    if custom_osm_filter is None:
        request_filter = osm_filter(network_type)
    else:
        request_filter = custom_osm_filter

    response_jsons_list = []
    response_jsons = []

    # server memory allocation in bytes formatted for Overpass API query
    if memory is None:
        maxsize = ''
    else:
        maxsize = '[maxsize:{}]'.format(memory)

    # define the Overpass API query
    # way["highway"] denotes ways with highway keys and {filters} returns
    # ways with the requested key/value. the '>' makes it recurse so we get
    # ways and way nodes. maxsize is in bytes.

    # turn bbox into a polygon and project to local UTM
    polygon = Polygon([(lng_max, lat_min), (lng_min, lat_min),
                       (lng_min, lat_max), (lng_max, lat_max)])
    geometry_proj, crs_proj = project_geometry(polygon,
                                               crs={'init': 'epsg:4326'})

    # subdivide the bbox area poly if it exceeds the max area size
    # (in meters), then project back to WGS84
    geometry_proj_consolidated_subdivided = consolidate_subdivide_geometry(
        geometry_proj, max_query_area_size=max_query_area_size)
    geometry, crs = project_geometry(geometry_proj_consolidated_subdivided,
                                     crs=crs_proj, to_latlong=True)
    log('Requesting network data within bounding box from Overpass API '
        'in {:,} request(s)'.format(len(geometry)))
    start_time = time.time()

    # loop through each polygon in the geometry
    for poly in geometry:
        # represent bbox as lng_max, lat_min, lng_min, lat_max and round
        # lat-longs to 8 decimal places to create
        # consistent URL strings
        lng_max, lat_min, lng_min, lat_max = poly.bounds
        query_template = '[out:json][timeout:{timeout}]{maxsize};' \
                         '(way["highway"]' \
                         '{filters}({lat_min:.8f},{lng_max:.8f},' \
                         '{lat_max:.8f},{lng_min:.8f});>;);out;'
        query_str = query_template.format(lat_max=lat_max, lat_min=lat_min,
                                          lng_min=lng_min, lng_max=lng_max,
                                          filters=request_filter,
                                          timeout=timeout, maxsize=maxsize)
        response_json = overpass_request(data={'data': query_str},
                                         timeout=timeout)

        response_jsons_list.append(response_json)

    log('Downloaded OSM network data within bounding box from Overpass '
        'API in {:,} request(s) and'
        ' {:,.2f} seconds'.format(len(geometry), time.time()-start_time))

    # stitch together individual json results
    for json in response_jsons_list:
        try:
            response_jsons.extend(json['elements'])
        except KeyError:
            pass

    # remove duplicate records resulting from the json stitching
    start_time = time.time()
    record_count = len(response_jsons)

    if record_count == 0:
        raise Exception('Query resulted in no data. Check your query '
                        'parameters: {}'.format(query_str))
    else:
        response_jsons_df = pd.DataFrame.from_records(response_jsons,
                                                      index='id')
        nodes = response_jsons_df[response_jsons_df['type'] == 'node']
        nodes = nodes[~nodes.index.duplicated(keep='first')]
        ways = response_jsons_df[response_jsons_df['type'] == 'way']
        ways = ways[~ways.index.duplicated(keep='first')]
        response_jsons_df = pd.concat([nodes, ways], axis=0)
        response_jsons_df.reset_index(inplace=True)
        response_jsons = response_jsons_df.to_dict(orient='records')
        if record_count - len(response_jsons) > 0:
            log('{:,} duplicate records removed. Took {:,.2f} seconds'.format(
                record_count - len(response_jsons), time.time() - start_time))

    return {'elements': response_jsons}


def overpass_request(data, pause_duration=None, timeout=180,
                     error_pause_duration=None):
    """
    Send a request to the Overpass API via HTTP POST and return the
    JSON response

    Parameters
    ----------
    data : dict or OrderedDict
        key-value pairs of parameters to post to Overpass API
    pause_duration : int
        how long to pause in seconds before requests, if None, will query
        Overpass API status endpoint
        to find when next slot is available
    timeout : int
        the timeout interval for the requests library
    error_pause_duration : int
        how long to pause in seconds before re-trying requests if error

    Returns
    -------
    response_json : dict
    """

    # define the Overpass API URL, then construct a GET-style URL
    url = 'http://www.overpass-api.de/api/interpreter'

    start_time = time.time()
    log('Posting to {} with timeout={}, "{}"'.format(url, timeout, data))
    response = requests.post(url, data=data, timeout=timeout)

    # get the response size and the domain, log result
    size_kb = len(response.content) / 1000.
    domain = re.findall(r'//(?s)(.*?)/', url)[0]
    log('Downloaded {:,.1f}KB from {} in {:,.2f} seconds'
        .format(size_kb, domain, time.time()-start_time))

    try:
        response_json = response.json()
        if 'remark' in response_json:
            log('Server remark: "{}"'.format(response_json['remark'],
                                             level=lg.WARNING))

    except Exception:
        # 429 = 'too many requests' and 504 = 'gateway timeout' from server
        # overload. handle these errors by recursively
        # calling overpass_request until a valid response is achieved
        if response.status_code in [429, 504]:
            # pause for error_pause_duration seconds before re-trying request
            if error_pause_duration is None:
                error_pause_duration = get_pause_duration()
            log('Server at {} returned status code {} and no JSON data. '
                'Re-trying request in {:.2f} seconds.'
                .format(domain, response.status_code, error_pause_duration),
                level=lg.WARNING)
            time.sleep(error_pause_duration)
            response_json = overpass_request(data=data,
                                             pause_duration=pause_duration,
                                             timeout=timeout)

        # else, this was an unhandled status_code, throw an exception
        else:
            log('Server at {} returned status code {} and no JSON data'
                .format(domain, response.status_code), level=lg.ERROR)
            raise Exception('Server returned no JSON data.\n{} {}\n{}'
                            .format(response, response.reason, response.text))

    return response_json


def get_pause_duration(recursive_delay=5, default_duration=10):
    """
    Check the Overpass API status endpoint to determine how long to wait until
    next slot is available.

    Parameters
    ----------
    recursive_delay : int
        how long to wait between recursive calls if server is currently
        running a query
    default_duration : int
        if fatal error, function falls back on returning this value

    Returns
    -------
    pause_duration : int
    """
    try:
        response = requests.get('http://overpass-api.de/api/status')
        status = response.text.split('\n')[3]
        status_first_token = status.split(' ')[0]
    except Exception:
        # if status endpoint cannot be reached or output parsed, log error
        # and return default duration
        log('Unable to query http://overpass-api.de/api/status',
            level=lg.ERROR)
        return default_duration

    try:
        # if first token is numeric, it indicates the number of slots
        # available - no wait required
        available_slots = int(status_first_token)
        pause_duration = 0
    except Exception:
        # if first token is 'Slot', it tells you when your slot will be free
        if status_first_token == 'Slot':
            utc_time_str = status.split(' ')[3]
            utc_time = date_parser.parse(utc_time_str).replace(tzinfo=None)
            pause_duration = math.ceil(
                (utc_time - dt.datetime.utcnow()).total_seconds())
            pause_duration = max(pause_duration, 1)

        # if first token is 'Currently', it is currently running a query so
        # check back in recursive_delay seconds
        elif status_first_token == 'Currently':
            time.sleep(recursive_delay)
            pause_duration = get_pause_duration()

        else:
            # any other status is unrecognized - log an error and return
            # default duration
            log('Unrecognized server status: "{}"'.format(status),
                level=lg.ERROR)
            return default_duration

    return pause_duration


def consolidate_subdivide_geometry(geometry, max_query_area_size):
    """
    Consolidate a geometry into a convex hull, then subdivide it into
    smaller sub-polygons if its area exceeds max size (in geometry's units).

    Parameters
    ----------
    geometry : shapely Polygon or MultiPolygon
        the geometry to consolidate and subdivide
    max_query_area_size : float
        max area for any part of the geometry, in the units the geometry is
        in: any polygon bigger will get divided up for multiple queries to
        the Overpass API (default is 50,000 * 50,000 units
        (ie, 50km x 50km in area, if units are meters))

    Returns
    -------
    geometry : Polygon or MultiPolygon
    """

    # let the linear length of the quadrats (with which to subdivide the
    # geometry) be the square root of max area size
    quadrat_width = math.sqrt(max_query_area_size)

    if not isinstance(geometry, (Polygon, MultiPolygon)):
        raise ValueError('Geometry must be a shapely Polygon or MultiPolygon')

    # if geometry is a MultiPolygon OR a single Polygon whose area exceeds
    # the max size, get the convex hull around the geometry
    if isinstance(
            geometry, MultiPolygon) or \
            (isinstance(
                geometry, Polygon) and geometry.area > max_query_area_size):
        geometry = geometry.convex_hull

    # if geometry area exceeds max size, subdivide it into smaller sub-polygons
    if geometry.area > max_query_area_size:
        geometry = quadrat_cut_geometry(geometry, quadrat_width=quadrat_width)

    if isinstance(geometry, Polygon):
        geometry = MultiPolygon([geometry])

    return geometry


def quadrat_cut_geometry(geometry, quadrat_width, min_num=3,
                         buffer_amount=1e-9):
    """
    Split a Polygon or MultiPolygon up into sub-polygons of a specified size,
    using quadrats.

    Parameters
    ----------
    geometry : shapely Polygon or MultiPolygon
        the geometry to split up into smaller sub-polygons
    quadrat_width : float
        the linear width of the quadrats with which to cut up the geometry
        (in the units the geometry is in)
    min_num : float
        the minimum number of linear quadrat lines (e.g., min_num=3 would
        produce a quadrat grid of 4 squares)
    buffer_amount : float
        buffer the quadrat grid lines by quadrat_width times buffer_amount

    Returns
    -------
    multipoly : shapely MultiPolygon
    """

    # create n evenly spaced points between the min and max x and y bounds
    lng_max, lat_min, lng_min, lat_max = geometry.bounds
    x_num = math.ceil((lng_min-lng_max) / quadrat_width) + 1
    y_num = math.ceil((lat_max-lat_min) / quadrat_width) + 1
    x_points = np.linspace(lng_max, lng_min, num=max(x_num, min_num))
    y_points = np.linspace(lat_min, lat_max, num=max(y_num, min_num))

    # create a quadrat grid of lines at each of the evenly spaced points
    vertical_lines = [LineString([(x, y_points[0]), (x, y_points[-1])])
                      for x in x_points]
    horizont_lines = [LineString([(x_points[0], y), (x_points[-1], y)])
                      for y in y_points]
    lines = vertical_lines + horizont_lines

    # buffer each line to distance of the quadrat width divided by 1 billion,
    # take their union, then cut geometry into pieces by these quadrats
    buffer_size = quadrat_width * buffer_amount
    lines_buffered = [line.buffer(buffer_size) for line in lines]
    quadrats = unary_union(lines_buffered)
    multipoly = geometry.difference(quadrats)

    return multipoly


def project_geometry(geometry, crs, to_latlong=False):
    """
    Project a shapely Polygon or MultiPolygon from WGS84 to UTM, or vice-versa

    Parameters
    ----------
    geometry : shapely Polygon or MultiPolygon
        the geometry to project
    crs : int
        the starting coordinate reference system of the passed-in geometry
    to_latlong : bool
        if True, project from crs to WGS84, if False, project
        from crs to local UTM zone

    Returns
    -------
    geometry_proj, crs : tuple (projected shapely geometry, crs of the
    projected geometry)
    """
    gdf = gpd.GeoDataFrame()
    gdf.crs = crs
    gdf.name = 'geometry to project'
    gdf['geometry'] = None
    gdf.loc[0, 'geometry'] = geometry
    gdf_proj = project_gdf(gdf, to_latlong=to_latlong)
    geometry_proj = gdf_proj['geometry'].iloc[0]
    return geometry_proj, gdf_proj.crs


def project_gdf(gdf, to_latlong=False, verbose=False):
    """
    Project a GeoDataFrame to the UTM zone appropriate for its geometries'
    centroid. The calculation works well for most latitudes,
    however it will not work well for some far northern locations.

    Parameters
    ----------
    gdf : GeoDataFrame
        the gdf to be projected to UTM
    to_latlong : bool
        if True, projects to WGS84 instead of to UTM

    Returns
    -------
    gdf : GeoDataFrame
    """
    assert len(gdf) > 0, 'You cannot project an empty GeoDataFrame.'
    start_time = time.time()

    if to_latlong:
        # if to_latlong is True, project the gdf to WGS84
        latlong_crs = {'init': 'epsg:4326'}
        projected_gdf = gdf.to_crs(latlong_crs)
        if not hasattr(gdf, 'name'):
            gdf.name = 'unnamed'
        if verbose:
            log('Projected the GeoDataFrame "{}" to EPSG 4326 in {:,.2f} '
                'seconds'.format(gdf.name, time.time()-start_time))
    else:
        # else, project the gdf to UTM
        # if GeoDataFrame is already in UTM, return it
        if (gdf.crs is not None) and ('proj' in gdf.crs) \
                and (gdf.crs['proj'] == 'utm'):
            return gdf

        # calculate the centroid of the union of all the geometries in the
        # GeoDataFrame
        avg_longitude = gdf['geometry'].unary_union.centroid.x

        # calculate the UTM zone from this avg longitude and define the
        # UTM CRS to project
        utm_zone = int(math.floor((avg_longitude + 180) / 6.) + 1)
        utm_crs = {'datum': 'NAD83',
                   'ellps': 'GRS80',
                   'proj': 'utm',
                   'zone': utm_zone,
                   'units': 'm'}

        # project the GeoDataFrame to the UTM CRS
        projected_gdf = gdf.to_crs(utm_crs)
        if not hasattr(gdf, 'name'):
            gdf.name = 'unnamed'
        if verbose:
            log('Projected the GeoDataFrame "{}" to UTM-{} in {:,.2f} '
                'seconds'.format(gdf.name, utm_zone, time.time()-start_time))

    projected_gdf.name = gdf.name
    return projected_gdf


def process_node(e):
    """
    Process a node element entry into a dict suitable for going into a
    Pandas DataFrame.

    Parameters
    ----------
    e : dict
        individual node element in downloaded OSM json

    Returns
    -------
    node : dict

    """
    node = {'id': e['id'],
            'lat': e['lat'],
            'lon': e['lon']}

    if 'tags' in e:
        if e['tags'] is not np.nan:
            for t, v in list(e['tags'].items()):
                if t in config.settings.keep_osm_tags:
                    node[t] = v

    return node


def process_way(e):
    """
    Process a way element entry into a list of dicts suitable for going into
    a Pandas DataFrame.

    Parameters
    ----------
    e : dict
        individual way element in downloaded OSM json

    Returns
    -------
    way : dict
    waynodes : list of dict

    """
    way = {'id': e['id']}

    if 'tags' in e:
        if e['tags'] is not np.nan:
            for t, v in list(e['tags'].items()):
                if t in config.settings.keep_osm_tags:
                    way[t] = v

    # nodes that make up a way
    waynodes = []

    for n in e['nodes']:
        waynodes.append({'way_id': e['id'], 'node_id': n})

    return way, waynodes


def parse_network_osm_query(data):
    """
    Convert OSM query data to DataFrames of ways and way-nodes.

    Parameters
    ----------
    data : dict
        Result of an OSM query.

    Returns
    -------
    nodes, ways, waynodes : pandas.DataFrame

    """
    if len(data['elements']) == 0:
        raise RuntimeError('OSM query results contain no data.')

    nodes = []
    ways = []
    waynodes = []

    for e in data['elements']:
        if e['type'] == 'node':
            nodes.append(process_node(e))
        elif e['type'] == 'way':
            w, wn = process_way(e)
            ways.append(w)
            waynodes.extend(wn)

    nodes = pd.DataFrame.from_records(nodes, index='id')
    ways = pd.DataFrame.from_records(ways, index='id')
    waynodes = pd.DataFrame.from_records(waynodes, index='way_id')

    return (nodes, ways, waynodes)


def ways_in_bbox(lat_min, lng_min, lat_max, lng_max, network_type,
                 timeout=180, memory=None,
                 max_query_area_size=50*1000*50*1000,
                 custom_osm_filter=None):
    """
    Get DataFrames of OSM data in a bounding box.

    Parameters
    ----------
    lat_min : float
        southern latitude of bounding box
    lng_min : float
        eastern longitude of bounding box
    lat_max : float
        northern latitude of bounding box
    lng_max : float
        western longitude of bounding box
    network_type : {'walk', 'drive'}, optional
        Specify the network type where value of 'walk' includes roadways
        where pedestrians are allowed and pedestrian pathways and 'drive'
        includes driveable roadways.
    timeout : int
        the timeout interval for requests and to pass to Overpass API
    memory : int
        server memory allocation size for the query, in bytes. If none,
        server will use its default allocation size
    max_query_area_size : float
        max area for any part of the geometry, in the units the geometry is
        in: any polygon bigger will get divided up for multiple queries to
        Overpass API (default is 50,000 * 50,000 units (ie, 50km x 50km in
        area, if units are meters))
    custom_osm_filter : string, optional
        specify custom arguments for the way["highway"] query to OSM. Must
        follow Overpass API schema. For
        example to request highway ways that are service roads use:
        '["highway"="service"]'

    Returns
    -------
    nodes, ways, waynodes : pandas.DataFrame

    """
    return parse_network_osm_query(
        osm_net_download(lat_max=lat_max, lat_min=lat_min, lng_min=lng_min,
                         lng_max=lng_max, network_type=network_type,
                         timeout=timeout, memory=memory,
                         max_query_area_size=max_query_area_size,
                         custom_osm_filter=custom_osm_filter))


def intersection_nodes(waynodes):
    """
    Returns a set of all the nodes that appear in 2 or more ways.

    Parameters
    ----------
    waynodes : pandas.DataFrame
        Mapping of way IDs to node IDs as returned by `ways_in_bbox`.

    Returns
    -------
    intersections : set
        Node IDs that appear in 2 or more ways.

    """
    counts = waynodes.node_id.value_counts()
    return set(counts[counts > 1].index.values)


def node_pairs(nodes, ways, waynodes, two_way=True):
    """
    Create a table of node pairs with the distances between them.

    Parameters
    ----------
    nodes : pandas.DataFrame
        Must have 'lat' and 'lon' columns.
    ways : pandas.DataFrame
        Table of way metadata.
    waynodes : pandas.DataFrame
        Table linking way IDs to node IDs. Way IDs should be in the index,
        with a column called 'node_ids'.
    two_way : bool, optional
        Whether the routes are two-way. If True, node pairs will only
        occur once. Default is True.

    Returns
    -------
    pairs : pandas.DataFrame
        Will have columns of 'from_id', 'to_id', and 'distance'.
        The index will be a MultiIndex of (from id, to id).
        The distance metric is in meters.

    """
    start_time = time.time()

    def pairwise(l):
        return zip(islice(l, 0, len(l)), islice(l, 1, None))
    intersections = intersection_nodes(waynodes)
    waymap = waynodes.groupby(level=0, sort=False)
    pairs = []

    for id, row in ways.iterrows():
        nodes_in_way = waymap.get_group(id).node_id.values
        nodes_in_way = [x for x in nodes_in_way if x in intersections]

        if len(nodes_in_way) < 2:
            # no nodes to connect in this way
            continue

        for from_node, to_node in pairwise(nodes_in_way):
            if from_node != to_node:
                fn = nodes.loc[from_node]
                tn = nodes.loc[to_node]

                distance = round(gcd(fn.lat, fn.lon, tn.lat, tn.lon), 6)

                col_dict = {'from_id': from_node,
                            'to_id': to_node,
                            'distance': distance}

                for tag in config.settings.keep_osm_tags:
                    try:
                        col_dict.update({tag: row[tag]})
                    except KeyError:
                        pass

                pairs.append(col_dict)

                if not two_way:

                    col_dict = {'from_id': to_node,
                                'to_id': from_node,
                                'distance': distance}

                    for tag in config.settings.keep_osm_tags:
                        try:
                            col_dict.update({tag: row[tag]})
                        except KeyError:
                            pass

                    pairs.append(col_dict)

    pairs = pd.DataFrame.from_records(pairs)
    if pairs.empty:
        raise Exception('Query resulted in no connected node pairs. Check '
                        'your query parameters or bounding box')
    else:
        pairs.index = pd.MultiIndex.from_arrays([pairs['from_id'].values,
                                                 pairs['to_id'].values])
        log('Edge node pairs completed. Took {:,.2f} seconds'
            .format(time.time()-start_time))

        return pairs


def network_from_bbox(lat_min=None, lng_min=None, lat_max=None, lng_max=None,
                      bbox=None, network_type='walk', two_way=True,
                      timeout=180, memory=None,
                      max_query_area_size=50*1000*50*1000,
                      custom_osm_filter=None):
    """
    Make a graph network from a bounding lat/lon box composed of nodes and
    edges for use in Pandana street network accessibility calculations.
    You may either enter a lat/long box via the four lat_min,
    lng_min, lat_max, lng_max parameters or the bbox parameter as a tuple.

    Parameters
    ----------
    lat_min : float
        southern latitude of bounding box, if this parameter is used the bbox
        parameter should be None.
    lng_min : float
        eastern latitude of bounding box, if this parameter is used the bbox
        parameter should be None.
    lat_max : float
        northern longitude of bounding box, if this parameter is used the bbox
        parameter should be None.
    lng_max : float
        western longitude of bounding box, if this parameter is used the bbox
        parameter should be None.
    bbox : tuple
        Bounding box formatted as a 4 element tuple:
        (lng_max, lat_min, lng_min, lat_max)
        example: (-122.304611,37.798933,-122.263412,37.822802)
        a bbox can be extracted for an area using: the CSV format bbox from
        http://boundingbox.klokantech.com/. If this parameter is used the
        lat_min, lng_min, lat_max, lng_max parameters in this function
        should be None.
    network_type : {'walk', 'drive'}, optional
        Specify the network type where value of 'walk' includes roadways where
        pedestrians are allowed and pedestrian pathways and 'drive' includes
        driveable roadways. To use a custom definition see the
        custom_osm_filter parameter. Default is walk.
    two_way : bool, optional
        Whether the routes are two-way. If True, node pairs will only
        occur once.
    timeout : int, optional
        the timeout interval for requests and to pass to Overpass API
    memory : int, optional
        server memory allocation size for the query, in bytes. If none,
        server will use its default allocation size
    max_query_area_size : float, optional
        max area for any part of the geometry, in the units the geometry is
        in: any polygon bigger will get divided up for multiple queries to
        Overpass API (default is 50,000 * 50,000 units (ie, 50km x 50km in
        area, if units are meters))
    custom_osm_filter : string, optional
        specify custom arguments for the way["highway"] query to OSM. Must
        follow Overpass API schema. For
        example to request highway ways that are service roads use:
        '["highway"="service"]'

    Returns
    -------
    nodesfinal, edgesfinal : pandas.DataFrame

    """

    start_time = time.time()

    if bbox is not None:
        assert isinstance(bbox, tuple) \
               and len(bbox) == 4, 'bbox must be a 4 element tuple'
        assert (lat_min is None) and (lng_min is None) and \
               (lat_max is None) and (lng_max is None), \
            'lat_min, lng_min, lat_max and lng_max must be None ' \
            'if you are using bbox'

        lng_max, lat_min, lng_min, lat_max = bbox

    assert lat_min is not None, 'lat_min cannot be None'
    assert lng_min is not None, 'lng_min cannot be None'
    assert lat_max is not None, 'lat_max cannot be None'
    assert lng_max is not None, 'lng_max cannot be None'
    assert isinstance(lat_min, float) and isinstance(lng_min, float) and \
        isinstance(lat_max, float) and isinstance(lng_max, float), \
        'lat_min, lng_min, lat_max, and lng_max must be floats'

    nodes, ways, waynodes = ways_in_bbox(
        lat_min=lat_min, lng_min=lng_min, lat_max=lat_max, lng_max=lng_max,
        network_type=network_type, timeout=timeout,
        memory=memory, max_query_area_size=max_query_area_size,
        custom_osm_filter=custom_osm_filter)
    log('Returning OSM data with {:,} nodes and {:,} ways...'
        .format(len(nodes), len(ways)))

    edgesfinal = node_pairs(nodes, ways, waynodes, two_way=two_way)

    # make the unique set of nodes that ended up in pairs
    node_ids = sorted(set(edgesfinal['from_id'].unique())
                      .union(set(edgesfinal['to_id'].unique())))
    nodesfinal = nodes.loc[node_ids]
    nodesfinal = nodesfinal[['lon', 'lat']]
    nodesfinal.rename(columns={'lon': 'x', 'lat': 'y'}, inplace=True)
    nodesfinal['id'] = nodesfinal.index
    edgesfinal.rename(columns={'from_id': 'from', 'to_id': 'to'}, inplace=True)
    log('Returning processed graph with {:,} nodes and {:,} edges...'
        .format(len(nodesfinal), len(edgesfinal)))
    log('Completed OSM data download and Pandana node and edge table '
        'creation in {:,.2f} seconds'.format(time.time()-start_time))

    return nodesfinal, edgesfinal
