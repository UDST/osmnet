import pytest

import osmnet.config as config


@pytest.fixture(scope='module')
def default_config():
    # Default config settings
    return {'log_file': True,
            'log_name': 'osmnet',
            'log_filename': 'osmnet',
            'logs_folder': 'logs',
            'keep_osm_tags': ['name', 'ref', 'highway', 'service', 'bridge',
                              'tunnel', 'access', 'oneway', 'toll', 'lanes',
                              'maxspeed', 'hgv', 'hov', 'area', 'width',
                              'est_width', 'junction'],
            'log_console': False}


def test_config_defaults(default_config):
    settings = config.osmnet_config()
    config.format_check(settings.to_dict())
    assert settings.to_dict() == default_config
