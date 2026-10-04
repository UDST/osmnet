__version__ = "0.1.7"

version = __version__

# load.py reads __version__ for the User-Agent, so define it first
from .load import *  # noqa: E402
