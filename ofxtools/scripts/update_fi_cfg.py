#!/usr/bin/env python
# coding: utf-8
"""
Perform an OFX profile scan for the entire OFX Home list of FIs;
write working connection parameters to user config file with the
OFX Home id# as the server nickname
"""


# stdlib imports
import configparser
from configparser import ConfigParser
from collections import ChainMap
from xml.sax import saxutils
from typing import Mapping, MutableMapping, Optional


# local imports
from ofxtools import ofxhome
from ofxtools.scripts import ofxget


LibraryConfig = ConfigParser()
LibraryConfig.read(ofxget.CONFIGPATH)

# Map ofxhome_id: server_nick for all configs in library
known_servers = {LibraryConfig[sct]["ofxhome"]: sct for sct in LibraryConfig
                 if "ofxhome" in LibraryConfig[sct]}


def mk_server_cfg(args: ofxget.ArgType) -> configparser.SectionProxy:
    """
    Modified version of ofxget.mk_server_cfg()
    """
    server = args["server"]
    assert server

    if not LibraryConfig.has_section(server):
        LibraryConfig[server] = {}
    cfg = LibraryConfig[server]

    for opt in ("url", "version", "ofxhome", "org", "fid", "brokerid",
                "bankid", "pretty", "unclosedelements"):
        if opt in args:
            value = args[opt]
            default_value = ofxget.DEFAULTS[opt]
            if value != default_value and value not in ofxget.NULL_ARGS:
                cfg[opt] = ofxget.arg2config(opt, value)

    return cfg


def write_config(args: ofxget.ArgType) -> None:
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
        if lookup is None\
           or lookup.url is None\
           or ofxhome.ofx_invalid(lookup)\
           or ofxhome.ssl_invalid(lookup):
            continue

        url = lookup.url
        org = lookup.org
        fid = lookup.fid

        scan_results: ofxget.ScanResults = ofxget._scan_profile(
            url=url, org=org, fid=fid, timeout=10.0
        )

        v1, v2, signoninfo = scan_results
        if (not v2["versions"]) and (not v1["versions"]):
            continue

        format = ofxget._best_scan_format(scan_results)

        looked_up_data = {"ofxhome": ofxhome_id,
                          "url": url,
                          "org": org,
                          "fid": fid,
                          "brokerid": lookup.brokerid}

        lookup_name = saxutils.unescape(lookup.name)
        srvr_nick = known_servers.get(ofxhome_id, lookup_name)

        args = ChainMap({"server": srvr_nick}, looked_up_data, format)

        write_config(args)

        if not LibraryConfig.has_section("NAMES"):
            LibraryConfig["NAMES"] = {}
        names = LibraryConfig["NAMES"]

        ofxhome_id = args["ofxhome"]
        assert ofxhome_id

        if ofxhome_id not in names:
            names[ofxhome_id] = lookup_name


if __name__ == "__main__":
    main()
