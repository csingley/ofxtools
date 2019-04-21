#!/usr/bin/env python
"""
Interface with http://ofxhome.com
"""
# stdlib imports
import datetime
import xml.etree.ElementTree as ET
import urllib
from xml.sax import saxutils
#  from os import path
#  import csv
#  import concurrent.futures

# local imports
#  from ofxtools.Client import OFXClient


class OFXHomeLookup:
    query_url = "http://www.ofxhome.com/api.php?{}"
    valid_days = 90

    def __init__(self, id):
        self.id = id
        params = urllib.parse.urlencode({'lookup': id})
        query_url = self.query_url.format(params)
        with urllib.request.urlopen(query_url) as f:
            response = f.read()
            try:
                self.xml = ET.fromstring(response)
            except Exception as exc:
                print(response)
                return

        self.name = self._read("name")
        self.fid = self._read("fid")
        self.org = self._read("org")
        self.url = self._read("url")
        self.brokerid = self._read("brokerid")
        self.ofxfail = bool(int(self._read("ofxfail")))
        self.sslfail = bool(int(self._read("sslfail")))
        self.lastofxvalidation = self._read_date("lastofxvalidation")
        self.lastsslvalidation = self._read_date("lastsslvalidation")

    def _read(self, attr):
        child = self.xml.find(attr)
        if child is not None:
            text = child.text
            if text:
                text = saxutils.unescape(text)
            return text

    def _read_date(self, attr):
        child = self.xml.find(attr)
        if child is not None:
            text = child.text
            if text:
                text = datetime.datetime.fromisoformat(text)
            return text

    @property
    def ofx_valid(self):
        now = datetime.datetime.now()
        return (not self.ofxfail) and (now - self.lastofxvalidation) < datetime.timedelta(days=self.valid_days)

    @property
    def ssl_valid(self):
        now = datetime.datetime.now()
        return (not self.sslfail) and (now - self.lastsslvalidation)  < datetime.timedelta(days=self.valid_days)

    def __repr__(self):
        template = "id={id}, name='{name}', fid='{fid}', org='{org}'"
        if self.brokerid:
            template += ", brokerid='{brokerid}'"
        filled = template.format(**self.__dict__)
        return "<{}({})>".format(self.__class__.__name__, filled)
