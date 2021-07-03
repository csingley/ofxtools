#!/usr/bin/env python
"""
Interface with http://ofxhome.com API
"""


__all__ = [
    "URL",
    "VALID_DAYS",
    "OFXServer",
    "list_institutions",
    "lookup",
    "ofx_invalid",
    "ssl_invalid",
]


# stdlib imports
from collections import OrderedDict
import datetime
import xml.etree.ElementTree as ET
from xml.sax import saxutils
import urllib
import urllib.error as urllib_error
import urllib.parse as urllib_parse
import re
from typing import Dict, NamedTuple, Optional, Union, Mapping, Match


URL = "http://www.ofxhome.com/api.php"
VALID_DAYS = 90


FID_REGEX = re.compile(r"<fid>([^<]*)</fid>")


class OFXServer(NamedTuple):
    """Container for an OFX Home FI record"""

    id: Optional[str] = None
    name: Optional[str] = None
    fid: Optional[str] = None
    org: Optional[str] = None
    url: Optional[str] = None
    brokerid: Optional[str] = None
    ofxfail: Optional[bool] = True
    sslfail: Optional[bool] = True
    lastofxvalidation: Optional[datetime.datetime] = None
    lastsslvalidation: Optional[datetime.datetime] = None
    profile: Optional[Dict[str, Union[str, bool]]] = None


def list_institutions() -> Mapping[str, str]:
    query = _make_query(all="yes")
    with urllib.request.urlopen(query) as f:
        response = f.read()

    return {
        fi.get("id").strip(): fi.get("name").strip()  # type: ignore
        for fi in ET.fromstring(response)
    }


def lookup(id: str) -> Optional[OFXServer]:
    etree = fetch_fi_xml(id)
    if etree is None:
        return None

    converters = {
        "ofxfail": _convert_bool,
        "sslfail": _convert_bool,
        "lastofxvalidation": _convert_dt,
        "lastsslvalidation": _convert_dt,
        "profile": _convert_profile,
    }

    # mypy doesn't accept NamedTuple(**kwargs); use OrderedDict as workaround
    attrs = [(e.tag, converters.get(e.tag, _convert_str)(e)) for e in etree]
    attrs.insert(0, ("id", etree.attrib["id"]))
    return OFXServer(**OrderedDict(attrs))


def fetch_fi_xml(id: str) -> Optional[ET.Element]:
    if not id:
        return None

    query = _make_query(lookup=id)
    try:
        with urllib.request.urlopen(query) as f:
            response = f.read()
    except urllib_error.URLError:
        return None

    try:
        etree = ET.fromstring(response)
    except ET.ParseError:
        # OFX Home fails to escape XML control characters for <FID>
        response_ = FID_REGEX.sub(_escape_fid, response.decode())
        etree = ET.fromstring(response_)
    return etree


def ofx_invalid(srvr: OFXServer, valid_days: Optional[int] = None) -> bool:
    if srvr.ofxfail:
        return True
    if srvr.lastofxvalidation is None:
        return True
    if valid_days is None:
        valid_days = VALID_DAYS
    now = datetime.datetime.now()
    if (now - srvr.lastofxvalidation) > datetime.timedelta(days=valid_days):
        return True

    return False


def ssl_invalid(srvr: OFXServer, valid_days: Optional[int] = None) -> bool:
    if srvr.sslfail:
        return True
    if srvr.lastsslvalidation is None:
        return True
    if valid_days is None:
        valid_days = VALID_DAYS
    now = datetime.datetime.now()
    if (now - srvr.lastsslvalidation) > datetime.timedelta(days=valid_days):
        return True

    return False


def _make_query(**kwargs: str) -> str:
    params = urllib_parse.urlencode(kwargs)
    return "{}?{}".format(URL, params)


def _convert_str(elem: ET.Element) -> Optional[str]:
    text = elem.text
    if text:
        return saxutils.unescape(text).strip()
    return None


def _convert_dt(elem: ET.Element) -> Optional[datetime.datetime]:
    text = elem.text
    if text:
        return datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    return None


def _convert_bool(elem: ET.Element) -> Optional[bool]:
    text = elem.text
    if text:
        return bool(int(text))
    return None


def _convert_profile(elem: ET.Element) -> Dict[str, Union[str, bool]]:
    def convert_maybe_bool(key: str, val: str) -> Union[str, bool]:
        if key.endswith("msgset"):
            return {"true": True, "false": False}[val]
        return saxutils.unescape(val)

    return {k: convert_maybe_bool(k, v) for k, v in elem.attrib.items()}


def _escape_fid(match: Match) -> str:
    fid = saxutils.escape(match.group(1))
    return "<fid>{}</fid>".format(fid)
