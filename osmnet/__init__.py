__version__ = "0.2.dev0"

version = __version__

# load.py reads __version__ for the User-Agent, so define it first
from .load import *  # noqa: E402
