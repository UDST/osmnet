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
from osmnet import __version__
from osmnet.utils import log, great_circle_dist as gcd

# Overpass rejects requests without a descriptive User-Agent (HTTP 406)
USER_AGENT = 'osmnet/{} (+https://github.com/UDST/osmnet)'.format(
    __version__)
OVERPASS_STATUS_URL = 'https://overpass-api.de/api/status'


class OverpassRetryError(Exception):
    """
    Raised when the Overpass API keeps returning 429/504 after the
    maximum number of retries.
    """
    pass


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
        Returns response_json as a value of dict with key 'elements'
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
                                               crs="EPSG:4326")

    # subdivide the bbox area poly if it exceeds the max area size
    # (in meters), then project back to WGS84
    geometry_proj_consolidated_subdivided = consolidate_subdivide_geometry(
        geometry_proj, max_query_area_size=max_query_area_size)
    geometry, crs = project_geometry(geometry_proj_consolidated_subdivided,
                                     crs=crs_proj, to_latlong=True)
    log('Requesting network data within bounding box from Overpass API '
        'in {:,} request(s)'.format(len(geometry.geoms)))
    start_time = time.time()

    # loop through each polygon in the geometry
    for poly in geometry.geoms:
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
        ' {:,.2f} seconds'.format(len(geometry.geoms), time.time()-start_time))

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
                     error_pause_duration=None, max_retries=5):
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
    max_retries : int
        how many times to re-try the request after a 429 or 504 response
        before raising OverpassRetryError

    Returns
    -------
    response_json : dict
    """

    # define the Overpass API URL, then construct a GET-style URL
    url = 'https://www.overpass-api.de/api/interpreter'
    headers = {
        "User-Agent": USER_AGENT
    }

    # 429 = 'too many requests' and 504 = 'gateway timeout' from server
    # overload. handle these errors by re-trying the request, at most
    # max_retries times
    for attempt in range(max_retries + 1):
        start_time = time.time()
        log('Posting to {} with timeout={}, "{}"'.format(url, timeout, data))
        response = requests.post(
            url,
            data=data,
            headers=headers,
            timeout=timeout,
        )

        # get the response size and the domain, log result
        size_kb = len(response.content) / 1000.
        domain = re.findall(r'(?s)//(.*?)/', url)[0]
        log('Downloaded {:,.1f}KB from {} in {:,.2f} seconds'
            .format(size_kb, domain, time.time()-start_time))

        try:
            response_json = response.json()
            if 'remark' in response_json:
                log('Server remark: "{}"'.format(response_json['remark'],
                                                 level=lg.WARNING))
            return response_json

        except Exception:
            # else, this was an unhandled status_code, throw an exception
            if response.status_code not in [429, 504]:
                log('Server at {} returned status code {} and no JSON data'
                    .format(domain, response.status_code), level=lg.ERROR)
                raise Exception('Server returned no JSON data.\n{} {}\n{}'
                                .format(response, response.reason,
                                        response.text))

        if attempt == max_retries:
            break

        # pause for error_pause_duration seconds before re-trying request
        pause = error_pause_duration
        if pause is None:
            pause = get_pause_duration()
        log('Server at {} returned status code {} and no JSON data. '
            'Re-trying request in {:.2f} seconds (retry {} of {}).'
            .format(domain, response.status_code, pause, attempt + 1,
                    max_retries),
            level=lg.WARNING)
        time.sleep(pause)

    log('Server at {} returned status code {} after {} retries; giving up'
        .format(domain, response.status_code, max_retries), level=lg.ERROR)
    raise OverpassRetryError(
        'Overpass API at {} still returned status code {} after {} '
        'retries.'.format(domain, response.status_code, max_retries))


def _parse_overpass_status(text):
    """
    Parse the text of the Overpass API /api/status page.

    The relevant line is found by its content, not its position, because the
    page layout has changed over time (e.g. the 'Rate limit' and
    'Announced endpoint' lines).

    Parameters
    ----------
    text : str
        body of the /api/status response

    Returns
    -------
    status : tuple
        ('available', n_slots), ('slot', seconds until the next slot is
        free), ('busy', None) if all slots are taken by running queries, or
        (None, None) if the text is not recognized
    """
    lines = [line.strip() for line in text.splitlines()]

    # "2 slots available now."
    for line in lines:
        match = re.match(r'^(\d+)\s+slots?\s+available', line)
        if match:
            return 'available', int(match.group(1))

    # "Slot available after: 2026-10-04T12:20:01Z, in 107 seconds."
    # there is one such line per busy slot; use the earliest
    waits = []
    for line in lines:
        if not line.startswith('Slot'):
            continue
        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)', line)
        if match:
            utc_time = date_parser.parse(match.group(1))
            now = dt.datetime.now(dt.timezone.utc)
            waits.append(math.ceil((utc_time - now).total_seconds()))
    if waits:
        return 'slot', max(min(waits), 1)

    # no free slot and no release time: "Currently running queries ..."
    for line in lines:
        if line.startswith('Currently'):
            return 'busy', None

    return None, None


def get_pause_duration(recursive_delay=5, default_duration=10,
                       max_retries=5):
    """
    Check the Overpass API status endpoint to determine how long to wait until
    next slot is available.

    Parameters
    ----------
    recursive_delay : int
        how long to wait between status checks if server is currently
        running a query
    default_duration : int
        if fatal error, function falls back on returning this value
    max_retries : int
        how many times to re-check the status while the server is busy
        before falling back on default_duration

    Returns
    -------
    pause_duration : int
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(OVERPASS_STATUS_URL,
                                    headers={'User-Agent': USER_AGENT},
                                    timeout=30)
            response.raise_for_status()
            kind, value = _parse_overpass_status(response.text)
        except Exception:
            # if status endpoint cannot be reached or output parsed, log
            # error and return default duration
            log('Unable to query {}'.format(OVERPASS_STATUS_URL),
                level=lg.ERROR)
            return default_duration

        # slots available - no wait required
        if kind == 'available':
            return 0

        # the status tells you when your slot will be free
        if kind == 'slot':
            return value

        if kind is None:
            # any other status is unrecognized - log an error and return
            # default duration
            log('Unrecognized server status: "{}"'.format(response.text),
                level=lg.ERROR)
            return default_duration

        # the server is currently running queries, so check back in
        # recursive_delay seconds
        if attempt < max_retries:
            time.sleep(recursive_delay)

    log('Overpass server still busy after {} status checks; pausing {} '
        'seconds'.format(max_retries, default_duration), level=lg.WARNING)
    return default_duration


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
    geometry : Shapely Polygon or MultiPolygon
    """

    # let the linear length of the quadrats (with which to subdivide the
    # geometry) be the square root of max area size
    quadrat_width = math.sqrt(max_query_area_size)

    if not isinstance(geometry, (Polygon, MultiPolygon)):
        raise ValueError('Geometry must be a Shapely Polygon or MultiPolygon')

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
    multipoly : Shapely MultiPolygon
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
    geometry : shapely.geometry.Polygon or shapely.geometry.MultiPolygon
        the geometry to project
    crs : string or pyproj.CRS
        the starting coordinate reference system of the passed-in geometry
        such as "EPSG:4326"
    to_latlong : bool, optional
        if True, project from crs to WGS84, if False, project
        from crs to local UTM zone

    Returns
    -------
    geometry_proj, crs : tuple (projected Shapely geometry, crs of the
    projected geometry)
    """
    gdf = gpd.GeoDataFrame(geometry=[geometry], crs=crs)
    gdf_proj = project_gdf(gdf, to_latlong=to_latlong)
    geometry_proj = gdf_proj['geometry'].iloc[0]
    return geometry_proj, gdf_proj.crs


def project_gdf(gdf, to_crs=None, to_latlong=False):
    """
    Project a GeoDataFrame from its current CRS to another.
    If to_crs is None, project to the UTM CRS for the UTM zone in which the
    GeoDataFrame's centroid lies. Otherwise project to the CRS defined by
    to_crs. The simple UTM zone calculation in this function works well for
    most latitudes, but may not work for some extreme northern locations like
    Svalbard or far northern Norway. If the GeoDataFrame is already in UTM, it
    will be returned untouched.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        the GeoDataFrame to be projected
    to_crs : string or pyproj.CRS
        if None, project to UTM zone in which gdf's centroid lies, otherwise
        project to this CRS
    to_latlong : bool
        if True, project to epsg:4326 and ignore to_crs

    Returns
    -------
    gdf_proj : geopandas.GeoDataFrame
        the projected GeoDataFrame
    """
    if gdf.crs is None or len(gdf) < 1:
        raise ValueError(
            "GeoDataFrame must have a valid CRS and cannot be empty")

    # if to_latlong is True, project the gdf to latlong
    if to_latlong:
        gdf_proj = gdf.to_crs(4326)

    # else if to_crs was passed-in, project gdf to this CRS
    elif to_crs is not None:
        gdf_proj = gdf.to_crs(to_crs)

    # otherwise, automatically project the gdf to UTM
    else:
        if gdf.crs.is_projected:
            raise ValueError(
                "Geometry must be unprojected to calculate UTM zone")

        # calculate longitude of centroid of union of all geometries in gdf
        avg_lng = gdf["geometry"].unary_union.centroid.x

        # calculate UTM zone from avg longitude to define CRS to project to
        utm_zone = int(math.floor((avg_lng + 180) / 6.0) + 1)
        utm_crs = ('+proj=utm +zone={} +ellps=WGS84 '
                   '+datum=WGS84 +units=m +no_defs'.format(utm_zone))

        # project the GeoDataFrame to the UTM CRS
        gdf_proj = gdf.to_crs(utm_crs)

    return gdf_proj


def process_node(e):
    """
    Process a node element entry into a dict suitable for going into a
    Pandas DataFrame.

    Parameters
    ----------
    node : dict
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
    (nodes, ways, waynodes) : pandas.DataFrame
        nodes, ways, waynodes as a tuple of pandas.DataFrames

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

    def pairwise(ls):
        return zip(islice(ls, 0, len(ls)), islice(ls, 1, None))
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
        eastern longitude of bounding box, if this parameter is used the bbox
        parameter should be None.
    lat_max : float
        northern latitude of bounding box, if this parameter is used the bbox
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
