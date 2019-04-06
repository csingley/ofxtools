# coding: utf-8
""" Unit tests for models.signon """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import STATUS
from ofxtools.models.signon import (
    FI,
    SONRQ,
    SONRS,
)
from ofxtools.models.i18n import LANG_CODES
from ofxtools.utils import UTC


# test imports
import base


class FiTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ("FID",)

    @property
    def root(self):
        root = Element("FI")
        SubElement(root, "ORG").text = "IBLLC-US"
        SubElement(root, "FID").text = "4705"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FI)
        self.assertEqual(root.org, "IBLLC-US")
        self.assertEqual(root.fid, "4705")


class SonrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTCLIENT", "LANGUAGE", "APPID", "APPVER"]
    optionalElements = [
        "FI",
        "USERKEY",
        "GENUSERKEY",
        "SESSCOOKIE",
        "APPKEY",
        "CLIENTUID",
        "USERCRED1",
        "USERCRED2",
        "AUTHTOKEN",
        "ACCESSKEY",
    ]

    @property
    def root(self):
        root = Element("SONRQ")
        SubElement(root, "DTCLIENT").text = "20051029101003"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        SubElement(root, "GENUSERKEY").text = "N"
        SubElement(root, "LANGUAGE").text = "ENG"
        fi = FiTestCase().root
        root.append(fi)
        SubElement(root, "SESSCOOKIE").text = "BADA55"
        SubElement(root, "APPID").text = "QWIN"
        SubElement(root, "APPVER").text = "1500"
        SubElement(root, "APPKEY").text = "CAFEBABE"
        SubElement(root, "CLIENTUID").text = "DEADBEEF"
        SubElement(root, "USERCRED1").text = "Something"
        SubElement(root, "USERCRED2").text = "Something else"
        SubElement(root, "AUTHTOKEN").text = "line noise"
        SubElement(root, "ACCESSKEY").text = "CAFEBABE"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRQ)
        self.assertEqual(root.dtclient, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        self.assertEqual(root.userkey, "DEADBEEF")
        self.assertEqual(root.genuserkey, False)
        self.assertEqual(root.language, "ENG")
        self.assertIsInstance(root.fi, FI)
        self.assertEqual(root.sesscookie, "BADA55")
        self.assertEqual(root.appid, "QWIN")
        self.assertEqual(root.appver, "1500")
        self.assertEqual(root.clientuid, "DEADBEEF")
        self.assertEqual(root.usercred1, "Something")
        self.assertEqual(root.usercred2, "Something else")
        self.assertEqual(root.authtoken, "line noise")
        self.assertEqual(root.accesskey, "CAFEBABE")

    def testOneOf(self):
        self.oneOfTest("LANGUAGE", LANG_CODES)


class SonrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("STATUS", "DTSERVER")
    optionalElements = (
        "USERKEY",
        "TSKEYEXPIRE",
        "DTPROFUP",
        "DTACCTUP",
        "FI",
        "SESSCOOKIE",
        "ACCESSKEY",
    )

    @property
    def root(self):
        root = Element("SONRS")
        status = base.StatusTestCase().root
        root.append(status)
        SubElement(root, "DTSERVER").text = "20051029101003"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        SubElement(root, "TSKEYEXPIRE").text = "20051231"
        SubElement(root, "LANGUAGE").text = "ENG"
        SubElement(root, "DTPROFUP").text = "20050101"
        SubElement(root, "DTACCTUP").text = "20050102"
        fi = FiTestCase().root
        root.append(fi)
        SubElement(root, "SESSCOOKIE").text = "BADA55"
        SubElement(root, "ACCESSKEY").text = "CAFEBABE"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRS)
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.dtserver, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        self.assertEqual(root.userkey, "DEADBEEF")
        self.assertEqual(root.tskeyexpire, datetime(2005, 12, 31, tzinfo=UTC))
        self.assertEqual(root.language, "ENG")
        self.assertEqual(root.dtprofup, datetime(2005, 1, 1, tzinfo=UTC))
        self.assertEqual(root.dtacctup, datetime(2005, 1, 2, tzinfo=UTC))
        self.assertIsInstance(root.fi, FI)
        self.assertEqual(root.sesscookie, "BADA55")
        self.assertEqual(root.accesskey, "CAFEBABE")

    def testConvertRemoveProprietaryTag(self):
        # Make sure SONRS.from_etree() removes proprietary tags
        root = deepcopy(self.root)
        SubElement(root, "INTU.BANKID").text = "12345678"

        sonrs = Aggregate.from_etree(root)
        self.assertIsInstance(sonrs, SONRS)
        # Converted Aggregate should still have 10 values, not 11
        self.assertEqual(len(sonrs._spec_repr), 10)

        self.assertIsInstance(sonrs.status, STATUS)
        self.assertEqual(sonrs.dtserver, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        self.assertEqual(sonrs.userkey, "DEADBEEF")
        self.assertEqual(sonrs.tskeyexpire, datetime(2005, 12, 31, tzinfo=UTC))
        self.assertEqual(sonrs.language, "ENG")
        self.assertEqual(sonrs.dtprofup, datetime(2005, 1, 1, tzinfo=UTC))
        self.assertEqual(sonrs.dtacctup, datetime(2005, 1, 2, tzinfo=UTC))
        self.assertIsInstance(sonrs.fi, FI)
        self.assertEqual(sonrs.sesscookie, "BADA55")
        self.assertEqual(sonrs.accesskey, "CAFEBABE")

    def testOneOf(self):
        self.oneOfTest("LANGUAGE", LANG_CODES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.org, "IBLLC-US")
        self.assertEqual(root.fid, "4705")


if __name__ == "__main__":
    unittest.main()
