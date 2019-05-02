# coding: utf-8
# stdlib imports
import os

# local imports
from ofxtools import utils

__all__ = ["CONFIGDIR", "USERCONFIGDIR"]


CONFIGDIR = utils.fixpath(os.path.dirname(__file__))


# Cross-platform specification of user configuration directory
if "APPDATA" in os.environ:  # Windows
    CONFIGHOME = os.environ["APPDATA"]
elif "XDG_CONFIG_HOME" in os.environ:  # Linux
    CONFIGHOME = os.environ["XDG_CONFIG_HOME"]
else:
    CONFIGHOME = os.path.join(os.environ["HOME"], ".config")


USERCONFIGDIR = os.path.join(utils.fixpath(CONFIGHOME), "ofxtools")
