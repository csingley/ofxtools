#!/usr/bin/env python
"""
Interface with http://ofxhome.com API
"""
# stdlib imports
from collections import namedtuple
import datetime
import xml.etree.ElementTree as ET
import urllib
from xml.sax import saxutils
import re


__all__ = ["URL", "VALID_DAYS", "OFXServer", "list_institutions", "lookup",
           "ofx_invalid", "ssl_invalid"]


URL = "http://www.ofxhome.com/api.php"
VALID_DAYS = 90

FID_REGEX = re.compile(r"<fid>([^<]*)</fid>")


OFXServer = namedtuple("OFXServer",
                       ["id", "name", "fid", "org", "url", "brokerid",
                        "ofxfail", "sslfail", "lastofxvalidation",
                        "lastsslvalidation", "profile"])
OFXServer.__new__.__defaults__ = (None, ) * len(OFXServer._fields)


def list_institutions():
    query = _make_query(all="yes")
    with urllib.request.urlopen(query) as f:
        response = f.read()

    return ET.fromstring(response)


def lookup(id):
    query = _make_query(lookup=id)
    try:
        with urllib.request.urlopen(query) as f:
            response = f.read()
            try:
                etree = ET.fromstring(response)
            except ET.ParseError:
                # OFX Home fails to escape XML control characters for <FID>
                response = FID_REGEX.sub(_escape_fid, response.decode())
                etree = ET.fromstring(response)
    except urllib.error.URLError as exc:
        return

    reader = {"ofxfail": _read_bool,
              "sslfail": _read_bool,
              "lastofxvalidation": _read_date,
              "lastsslvalidation": _read_date,
              "profile": _read_profile}

    attrs = {e.tag: reader.get(e.tag, _read)(e) for e in etree}
    return OFXServer(**attrs)


def ofx_invalid(srvr, valid_days=None):
    if srvr.ofxfail:
        return True

    valid_days = valid_days or VALID_DAYS
    now = datetime.datetime.now()
    if (now - srvr.lastofxvalidation) > datetime.timedelta(days=valid_days):
        return True

    return False


def ssl_invalid(srvr, valid_days=None):
    if srvr.sslfail:
        return True

    valid_days = valid_days or VALID_DAYS
    now = datetime.datetime.now()
    if (now - srvr.lastsslvalidation) > datetime.timedelta(days=valid_days):
        return True

    return False


def _make_query(**kwargs):
    params = urllib.parse.urlencode(kwargs)
    return "{}?{}".format(URL, params)


def _read(elem):
    text = elem.text or None
    if text:
        text = saxutils.unescape(text)
    return text


def _read_date(elem):
    text = elem.text or None
    if text:
        text = datetime.datetime.fromisoformat(text)
    return text


def _read_bool(elem):
    text = elem.text or None
    if text:
        text = bool(int(text))
    return text


def _read_profile(elem):
    attrib = elem.attrib
    for key, val in attrib.items():
        if key.endswith("msgset"):
            attrib[key] = {"true": True, "false": False}[val]
    return attrib


def _escape_fid(match):
    fid = saxutils.escape(match.group(1))
    return "<fid>{}</fid>".format(fid)
