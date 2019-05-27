#!/usr/bin/env python
# coding: utf-8
"""
Perform an OFX profile scan for the entire OFX Home list of FIs;
update config/fi.cfg

You probably don't want to run this script; it's for the library developers.

It takes a long time to run and generates lots of HTTP requests, and the output
is not at all stable so it needs to be checked.
"""


# stdlib imports
import configparser
from configparser import ConfigParser
from xml.sax import saxutils
from typing import Mapping, Optional, ChainMap
import logging


# local imports
from ofxtools import ofxhome, config
from ofxtools.scripts import ofxget


LibraryConfig = ConfigParser()
LibraryConfig.read(ofxget.CONFIGPATH)

if not LibraryConfig.has_section("NAMES"):
    LibraryConfig["NAMES"] = {}

# Map ofxhome_id: server_nick for all configs in library
known_servers = {
    LibraryConfig[sct]["ofxhome"]: sct
    for sct in LibraryConfig
    if "ofxhome" in LibraryConfig[sct]
}


def mk_server_cfg(args: ofxget.ArgsType) -> configparser.SectionProxy:
    """
    Stripped-down version of ofxget.mk_server_cfg()
    """
    server = args["server"]
    assert server

    if not LibraryConfig.has_section(server):
        LibraryConfig[server] = {}
    cfg = LibraryConfig[server]

    for opt, opt_type in ofxget.CONFIGURABLE_SRVR.items():
        if opt in args:
            value = args[opt]
            default_value = ofxget.DEFAULTS[opt]
            if value != default_value and value not in ofxget.NULL_ARGS:
                cfg[opt] = ofxget.arg2config(opt, opt_type, value)

    return cfg


def write_config(args: ofxget.ArgsType) -> None:
    """
    Modified version of ofxget.write_config()
    """
    mk_server_cfg(args)

    with open(ofxget.CONFIGPATH, "w") as f:
        LibraryConfig.write(f)


def main():
    fis: Mapping[str, str] = ofxhome.list_institutions()
    for ofxhome_id in fis.keys():
        print("Scanning {}".format(ofxhome_id))

        lookup: Optional[ofxhome.OFXServer] = ofxhome.lookup(ofxhome_id)
        if lookup is None or lookup.url is None:
            continue

        url = lookup.url
        org = lookup.org
        fid = lookup.fid

        lookup_name = saxutils.unescape(lookup.name)
        srvr_nick = known_servers.get(ofxhome_id, lookup_name)

        ofxhome_id = lookup.id
        assert ofxhome_id
        names = LibraryConfig["NAMES"]
        if ofxhome_id not in names:
            names[ofxhome_id] = lookup_name

        if ofxhome.ofx_invalid(lookup) or ofxhome.ssl_invalid(lookup):
            blank_fmt = {"versions": [], "formats": {}}
            scan_results = (blank_fmt, blank_fmt, {})
        else:
            scan_results: ofxget.ScanResults = ofxget._scan_profile(
                url=url, org=org, fid=fid, timeout=10.0
            )

        v1, v2, _ = scan_results
        if (not v2["versions"]) and (not v1["versions"]):
            # If no OFX response, blank the server config
            LibraryConfig[srvr_nick] = {"ofxhome": ofxhome_id}
            continue

        format = ofxget._best_scan_format(scan_results)

        looked_up_data = {
            "ofxhome": ofxhome_id,
            "url": url,
            "org": org,
            "fid": fid,
            "brokerid": lookup.brokerid,
        }

        args = ChainMap({"server": srvr_nick}, looked_up_data, format)
        write_config(args)


LOG_LEVELS = {0: logging.WARN, 1: logging.INFO, 2: logging.DEBUG}


if __name__ == "__main__":
    from argparse import ArgumentParser

    argparser = ArgumentParser(description="Scan all FIs; update fi.cfg")
    argparser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Give more output (option can be repeated)",
    )
    args = argparser.parse_args()
    log_level = LOG_LEVELS.get(args.verbose, logging.DEBUG)
    config.configure_logging(log_level)
    main()
