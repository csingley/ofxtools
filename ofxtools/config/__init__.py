# coding: utf-8
# stdlib imports
import sys
import os
from pathlib import Path
import logging
import logging.config
import json


__all__ = [
    "CONFIGDIR",
    "USERCONFIGDIR",
    "LOGCONFIGPATH",
    "LOGPATH",
    "configure_logging",
]


CONFIGDIR = Path(__file__).parent.resolve()
HOME = Path.home().resolve()
PKGNAME = "ofxtools"


#  Cross-platform specification of user configuration directory
#  Mostly copied from:
#  https://github.com/ActiveState/appdirs
system = sys.platform.lower()
environ = os.environ

if system.startswith("win"):  # Windows
    if "APPDATA" in environ:
        CONFIGHOME = Path(environ["APPDATA"]).expanduser().resolve()
    else:
        CONFIGHOME = HOME / "AppData" / "Roaming"

    LOGDIR = CONFIGHOME / PKGNAME / "Logs"
    DATAHOME = CONFIGHOME

elif system.startswith("darwin"):  # Mac
    CONFIGHOME = HOME / "Library" / "Preferences"
    LOGDIR = HOME / "Library" / "Logs"
    DATAHOME = HOME / "Library" / "Application Support"

else:  # Linux
    if "XDG_CONFIG_HOME" in environ:
        CONFIGHOME = Path(environ["XDG_CONFIG_HOME"]).expanduser().resolve()
    else:
        CONFIGHOME = HOME / ".config"

    if "XDG_CACHE_HOME" in environ:
        LOGHOME = Path(environ["XDG_CACHE_HOME"]).expanduser().resolve()
    else:
        LOGHOME = HOME / ".cache"

    LOGDIR = LOGHOME / PKGNAME / "log"

    if "XDG_DATA_HOME" in environ:
        DATAHOME = Path(environ["XDG_DATA_HOME"]).expanduser().resolve()
    else:
        DATAHOME = HOME / ".local" / "share"


USERCONFIGDIR = CONFIGHOME / PKGNAME
USERCONFIGDIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOGCONFIGPATH = USERCONFIGDIR / "logging.json"
LOGPATH = LOGDIR / "ofxtools.log"

DATADIR = DATAHOME / PKGNAME
DATADIR.mkdir(parents=True, exist_ok=True)


def configure_logging(level=None):
    """
    Set up logging from user config file.
    Fall back to library default, and create user config file.
    Create directory to save logs from FileHandlers.
    """
    LOGDIR.mkdir(parents=True, exist_ok=True)

    config = None

    if LOGCONFIGPATH.exists():
        try:
            with open(LOGCONFIGPATH, "r") as f:
                config = json.load(f)
            assert config
        except Exception:
            config = None

    if config is None:
        config = DEFAULTLOGCONFIG
        with open(LOGCONFIGPATH, "w") as f:
            json.dump(config, f, indent=4)

    if level is not None:
        assert level in (
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        )
        for cfg in config["loggers"].values():
            cfg["level"] = level

    logging.config.dictConfig(config)
    logging.captureWarnings(True)


DEFAULTLOGCONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"style": "{", "format": "{name} [{levelname}] - {message}"},
        "timestamped": {
            "style": "{",
            "format": "{asctime} - {name} [{levelname}] - {message}",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": str(LOGPATH),
            "formatter": "timestamped",
        },
    },
    "loggers": {"": {"level": "WARNING", "handlers": ["console"]}},
}
