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
from ofxtools.utils import UTC, classproperty


# test imports
import base


class FiTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ("FID",)

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("FI")
        SubElement(root, "ORG").text = "IBLLC-US"
        SubElement(root, "FID").text = "4705"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return FI(org="IBLLC-US", fid="4705")


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
    oneOfs = {"LANGUAGE": LANG_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SONRQ")
        SubElement(root, "DTCLIENT").text = "20051029101003.000[0:GMT]"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        SubElement(root, "GENUSERKEY").text = "N"
        SubElement(root, "LANGUAGE").text = "ENG"
        root.append(FiTestCase.etree)
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

    @classproperty
    @classmethod
    def aggregate(cls):
        return SONRQ(dtclient=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
                     userkey="DEADBEEF", genuserkey=False, language="ENG",
                     fi=FiTestCase.aggregate, sesscookie="BADA55",
                     appid="QWIN", appver="1500", appkey="CAFEBABE",
                     clientuid="DEADBEEF", usercred1="Something",
                     usercred2="Something else", authtoken="line noise",
                     accesskey="CAFEBABE")


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
    oneOfs = {"LANGUAGE": LANG_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SONRS")
        root.append(base.StatusTestCase.etree)
        SubElement(root, "DTSERVER").text = "20051029101003.000[0:GMT]"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        SubElement(root, "TSKEYEXPIRE").text = "20051231000000.000[0:GMT]"
        SubElement(root, "LANGUAGE").text = "ENG"
        SubElement(root, "DTPROFUP").text = "20050101000000.000[0:GMT]"
        SubElement(root, "DTACCTUP").text = "20050102000000.000[0:GMT]"
        root.append(FiTestCase.etree)
        SubElement(root, "SESSCOOKIE").text = "BADA55"
        SubElement(root, "ACCESSKEY").text = "CAFEBABE"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SONRS(status=base.StatusTestCase.aggregate,
                     dtserver=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
                     userkey="DEADBEEF",
                     tskeyexpire=datetime(2005, 12, 31, tzinfo=UTC),
                     language="ENG", dtprofup=datetime(2005, 1, 1, tzinfo=UTC),
                     dtacctup=datetime(2005, 1, 2, tzinfo=UTC),
                     fi=FiTestCase.aggregate, sesscookie="BADA55",
                     accesskey="CAFEBABE")

    def testConvertRemoveProprietaryTag(cls):
        # Make sure SONRS.from_etree() removes proprietary tags
        root = deepcopy(cls.etree)
        SubElement(root, "INTU.BANKID").text = "12345678"

        sonrs = Aggregate.from_etree(root)
        cls.assertIsInstance(sonrs, SONRS)
        # Converted Aggregate should still have 10 values, not 11
        cls.assertEqual(len(sonrs._spec_repr), 10)

        cls.assertIsInstance(sonrs.status, STATUS)
        cls.assertEqual(sonrs.dtserver, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        cls.assertEqual(sonrs.userkey, "DEADBEEF")
        cls.assertEqual(sonrs.tskeyexpire, datetime(2005, 12, 31, tzinfo=UTC))
        cls.assertEqual(sonrs.language, "ENG")
        cls.assertEqual(sonrs.dtprofup, datetime(2005, 1, 1, tzinfo=UTC))
        cls.assertEqual(sonrs.dtacctup, datetime(2005, 1, 2, tzinfo=UTC))
        cls.assertIsInstance(sonrs.fi, FI)
        cls.assertEqual(sonrs.sesscookie, "BADA55")
        cls.assertEqual(sonrs.accesskey, "CAFEBABE")

    def testPropertyAliases(cls):
        root = Aggregate.from_etree(cls.etree)
        cls.assertEqual(root.org, "IBLLC-US")
        cls.assertEqual(root.fid, "4705")


if __name__ == "__main__":
    unittest.main()
