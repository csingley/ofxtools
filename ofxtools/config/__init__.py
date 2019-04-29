# coding: utf-8
# stdlib imports
import os
from configparser import ConfigParser

# local imports
from ofxtools import utils

__all__ = ['CONFIGHOME', 'USERCONFIGDIR', 'FICONFIG', 'USERFICONFIG',
           'OfxgetConfigParser']

HERE = utils.fixpath(os.path.dirname(__file__))

# Cross-platform specification of user configuration directory
if "APPDATA" in os.environ:  # Windows
    CONFIGHOME = os.environ["APPDATA"]
elif "XDG_CONFIG_HOME" in os.environ:  # Linux
    CONFIGHOME = os.environ["XDG_CONFIG_HOME"]
else:
    CONFIGHOME = os.path.join(os.environ["HOME"], ".config")

USERCONFIGDIR = os.path.join(utils.fixpath(CONFIGHOME), "ofxtools")

# Default FI configurations for ofxget
FICONFIG = os.path.join(HERE, "fi.cfg")

# User FI configurations for ofxget
USERFICONFIG = os.path.join(USERCONFIGDIR, "ofxget.cfg")


class OfxgetConfigParser(ConfigParser):
    """
    INI configuration for the ``ofxget`` CLI script.

    Loads package default FI configs and updates them with user app configs

    It also provides a list of configured FIs for use by the CLI --help.
    """

    def __init__(self):
        ConfigParser.__init__(self)

    def read(self, filenames=None):
        # Load default FI config
        with open(FICONFIG) as ficonfig:
            self.read_file(ficonfig)
        # Then load user configs
        filenames = filenames or USERFICONFIG
        return ConfigParser.read(self, filenames)

    @property
    def fi_index(self):
        """ List of configured FIs """
        return self.sections()
