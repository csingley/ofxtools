# coding: utf-8
""" Unit tests for ofxtools.ofxhome """

# stdlib imports
import unittest
from unittest.mock import patch
from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime

# local imports
from ofxtools import ofxhome


class ListInstitutionsTestCase(unittest.TestCase):
    def test(self):
        mock_xml = BytesIO(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <institutionlist>
            <institutionid name="American Express" id="1234"/>
            <institutionid name="Bank of America" id="2222"/>
            </institutionlist>
            """)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_xml
            lst = ofxhome.list_institutions()

        self.assertIsInstance(lst, ET.Element)
        self.assertEqual(lst.tag, "institutionlist")
        self.assertEqual(len((lst.text or "").strip()), 0)
        self.assertEqual(len((lst.tail or "").strip()), 0)
        self.assertEqual(lst.attrib, {})
        self.assertEqual(len(lst), 2)
        inst0, inst1 = lst[:]

        self.assertIsInstance(inst0, ET.Element)
        self.assertEqual(inst0.tag, "institutionid")
        self.assertEqual(len((inst0.text or "").strip()), 0)
        self.assertEqual(len((inst0.tail or "").strip()), 0)
        self.assertEqual(inst0.attrib,
                         {"name": "American Express", "id": "1234"})

        self.assertIsInstance(inst1, ET.Element)
        self.assertEqual(inst1.tag, "institutionid")
        self.assertEqual(len((inst1.text or "").strip()), 0)
        self.assertEqual(len((inst1.tail or "").strip()), 0)
        self.assertEqual(inst1.attrib,
                         {"name": "Bank of America", "id": "2222"})


class LookupTestCase(unittest.TestCase):
    def test(self):
        mock_xml = BytesIO(
            b"""<?xml version="1.0" encoding="utf-8"?>
            <institution id="424">
            <name>American Express Card</name>
            <fid>3101</fid>
            <org>AMEX</org>
            <url>https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload</url>
            <ofxfail>0</ofxfail>
            <sslfail>0</sslfail>
            <lastofxvalidation>2019-04-29 23:08:45</lastofxvalidation>
            <lastsslvalidation>2019-04-29 23:08:44</lastsslvalidation>
            <profile finame="American Express" addr1="777 American Expressway" city="Fort Lauderdale" state="Fla." postalcode="33337-0001" country="USA" csphone="1-800-AXP-7500  (1-800-297-7500)" url="https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload" signonmsgset="true" bankmsgset="true" creditcardmsgset="true"/>
            </institution>
            """)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_xml
            lookup = ofxhome.lookup("424")

        self.assertIsInstance(lookup, ofxhome.OFXServer)
        self.assertEqual(lookup.id, "424")
        self.assertEqual(lookup.name, "American Express Card")
        self.assertEqual(lookup.fid, "3101")
        self.assertEqual(lookup.org, "AMEX")
        self.assertEqual(lookup.url, "https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload")
        self.assertEqual(lookup.ofxfail, False)
        self.assertEqual(lookup.sslfail, False)
        self.assertEqual(lookup.lastofxvalidation, datetime(2019, 4, 29, 23, 8, 45))
        self.assertEqual(lookup.lastsslvalidation, datetime(2019, 4, 29, 23, 8, 44))
        self.assertEqual(lookup.profile,
                         {"finame": "American Express",
                          "addr1": "777 American Expressway",
                          "city": "Fort Lauderdale",
                          "state": "Fla.",
                          "postalcode": "33337-0001",
                          "country": "USA",
                          "csphone": "1-800-AXP-7500  (1-800-297-7500)",
                          "url": "https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload",
                          "signonmsgset": True,
                          "bankmsgset": True,
                          "creditcardmsgset": True})


class OfxInvalidTestCase(unittest.TestCase):
    pass


class SslInvalidTestCase(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
