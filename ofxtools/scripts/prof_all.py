#!/usr/bin/env python
# coding: utf-8
"""
Perform an OFX profile scan for the entire OFX Home list of FIs;
write working connection parameters to user config file with the
OFX Home id# as the server nickname
"""


# stdlib imports
from collections import ChainMap
from xml.sax import saxutils
from typing import Mapping, MutableMapping, Optional


# local imports
from ofxtools import ofxhome
from ofxtools.scripts import ofxget


def main():
    results: MutableMapping[str, ofxget.ScanResults] = {}

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

        results[ofxhome_id] = scan_results

        format = ofxget._best_scan_format(scan_results)

        looked_up_data = {"server": saxutils.unescape(lookup.name),
                          "ofxhome": ofxhome_id,
                          "url": url,
                          "org": org,
                          "fid": fid,
                          "brokerid": lookup.brokerid,
                          }
        args = ChainMap(looked_up_data, format)

        ofxget.write_config(args)

    return results


if __name__ == "__main__":
    main()
