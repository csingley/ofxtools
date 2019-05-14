# coding: utf-8
# stdlib imports
import sys
import os
from pathlib import Path

# local imports
from ofxtools import utils

__all__ = ["CONFIGDIR", "USERCONFIGDIR"]


CONFIGDIR = utils.fixpath(os.path.dirname(__file__))


# Cross-platform specification of user configuration directory
system = sys.platform.lower()
environ = os.environ

if system.startswith("win"):  # Windows
    if "APPDATA" in environ:
        CONFIGHOME = Path(environ["APPDATA"])
    else:
        CONFIGHOME = Path.home().joinpath("AppData").joinpath("Roaming")
elif system.startswith("darwin"):  # Mac
    CONFIGHOME = Path.home().joinpath("Library").joinpath("Preferences")
else:  # Linux
    if "XDG_CONFIG_HOME" in os.environ:
        CONFIGHOME = Path(environ["XDG_CONFIG_HOME"])
    else:
        CONFIGHOME = Path.home().joinpath(".config")


USERCONFIGDIR = CONFIGHOME.joinpath("ofxtools")
