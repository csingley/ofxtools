#!/usr/bin/env python
"""
Interface with http://ofxhome.com API
"""
# stdlib imports
from collections import OrderedDict, namedtuple
import datetime
import xml.etree.ElementTree as ET
import urllib
import urllib.error as urllib_error
import urllib.parse as urllib_parse
from xml.sax import saxutils
import re
from typing import Optional, Union


__all__ = ["URL", "VALID_DAYS", "OFXServer", "list_institutions", "lookup",
           "ofx_invalid", "ssl_invalid"]


URL = "http://www.ofxhome.com/api.php"
VALID_DAYS = 90

FID_REGEX = re.compile(r"<fid>([^<]*)</fid>")


OFXServer = namedtuple("OFXServer",
                       ["id", "name", "fid", "org", "url", "brokerid",
                        "ofxfail", "sslfail", "lastofxvalidation",
                        "lastsslvalidation", "profile"])
OFXServer.__new__.__defaults__ = (None, ) * len(OFXServer._fields)  # type: ignore


def list_institutions() -> OrderedDict:
    query = _make_query(all="yes")
    with urllib.request.urlopen(query) as f:
        response = f.read()

    return OrderedDict((fi.get("id"), fi.get("name"))
                       for fi in ET.fromstring(response))


def lookup(id: str) -> Optional[OFXServer]:
    query = _make_query(lookup=id)
    try:
        with urllib.request.urlopen(query) as f:
            response = f.read()
            try:
                etree = ET.fromstring(response)
            except ET.ParseError:
                # OFX Home fails to escape XML control characters for <FID>
                response_ = FID_REGEX.sub(_escape_fid, response.decode())
                etree = ET.fromstring(response_)
    except urllib_error.URLError as exc:
        return None

    reader = {"ofxfail": _read_bool,
              "sslfail": _read_bool,
              "lastofxvalidation": _read_date,
              "lastsslvalidation": _read_date,
              "profile": _read_profile}

    attrs = {e.tag: reader.get(e.tag, _read)(e) for e in etree}
    attrs["id"] = etree.attrib["id"]
    return OFXServer(**attrs)


def ofx_invalid(srvr: OFXServer, valid_days: Optional[int] = None) -> bool:
    if srvr.ofxfail:
        return True

    valid_days = valid_days or VALID_DAYS
    now = datetime.datetime.now()
    if (now - srvr.lastofxvalidation) > datetime.timedelta(days=valid_days):
        return True

    return False


def ssl_invalid(srvr: OFXServer, valid_days: Optional[int] = None) -> bool:
    if srvr.sslfail:
        return True

    valid_days = valid_days or VALID_DAYS
    now = datetime.datetime.now()
    if (now - srvr.lastsslvalidation) > datetime.timedelta(days=valid_days):
        return True

    return False


def _make_query(**kwargs: str) -> str:
    params = urllib_parse.urlencode(kwargs)
    return "{}?{}".format(URL, params)


def _read(elem: ET.Element) -> Optional[str]:
    text = elem.text
    if text:
        return saxutils.unescape(text)
    return None


def _read_date(elem: ET.Element) -> Optional[datetime.datetime]:
    text = elem.text
    if text:
        return datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    return None


def _read_bool(elem: ET.Element) -> Optional[bool]:
    text = elem.text
    if text:
        return bool(int(text))
    return None


def _read_profile(elem: ET.Element) -> dict:
    def convert_bool(key: str, val: str) -> Union[str, bool]:
        if key.endswith("msgset"):
            return {"true": True, "false": False}[val]
        return val

    return {k: convert_bool(k, v) for k, v in elem.attrib.items()}


def _escape_fid(match) -> str:
    fid = saxutils.escape(match.group(1))
    return "<fid>{}</fid>".format(fid)
