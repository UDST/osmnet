
def format_check(settings):
    """
    Check the format of a osmnet_config object.

    Parameters
    ----------
    settings : dict
        osmnet_config as a dictionary
    Returns
    -------
    Nothing
    """

    valid_keys = ['logs_folder', 'log_file', 'log_console', 'log_name',
                  'log_filename', 'keep_osm_tags']

    for key in list(settings.keys()):
        assert key in valid_keys, \
            ('{} not found in list of valid configuation keys').format(key)
        assert isinstance(key, str), ('{} must be a string').format(key)
        if key == 'keep_osm_tags':
            assert isinstance(settings[key], list), \
                ('{} must be a list').format(key)
            for value in settings[key]:
                assert all(isinstance(element, str) for element in value), \
                    'all elements must be a string'
        if key == 'log_file' or key == 'log_console':
            assert isinstance(settings[key], bool), \
                ('{} must be boolean').format(key)


class osmnet_config(object):
    """
    A set of configuration variables to initiate the configuration settings
    for osmnet.

    Parameters
    ----------
    logs_folder : str
        location to write log files
    log_file : bool
        if true, save log output to a log file in logs_folder
    log_console : bool
        if true, print log output to the console
    log_name : str
        name of the logger
    log_filename : str
        name of the log file
    keep_osm_tags : list
        list of OpenStreetMap tags to save from way elements and preserve in
        network edge table
    """

    def __init__(self,
                 logs_folder='logs',
                 log_file=True,
                 log_console=False,
                 log_name='osmnet',
                 log_filename='osmnet',
                 keep_osm_tags=['name', 'ref', 'highway', 'service', 'bridge',
                                'tunnel', 'access', 'oneway', 'toll', 'lanes',
                                'maxspeed', 'hgv', 'hov', 'area', 'width',
                                'est_width', 'junction']):

        self.logs_folder = logs_folder
        self.log_file = log_file
        self.log_console = log_console
        self.log_name = log_name
        self.log_filename = log_filename
        self.keep_osm_tags = keep_osm_tags

    def to_dict(self):
        """
        Return a dict representation of an osmnet osmnet_config instance.
        """
        return {'logs_folder': self.logs_folder,
                'log_file': self.log_file,
                'log_console': self.log_console,
                'log_name': self.log_name,
                'log_filename': self.log_filename,
                'keep_osm_tags': self.keep_osm_tags
                }


# instantiate the osmnet configuration object and check format
settings = osmnet_config()
format_check(settings.to_dict())
