# coding: utf-8
""" Unit tests for models/common.py """
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
#  from xml.etree.ElementTree import Element, SubElement
import xml.etree.ElementTree as ET


# local imports
import base
import test_models_i18n
from test_models_base import TESTAGGREGATE, TESTSUBAGGREGATE, TESTLIST

from ofxtools.models.base import Aggregate
from ofxtools.models.common import (
    STATUS,
    BAL,
    CURRENCY,
    OFXELEMENT,
    OFXEXTENSION,
    MSGSETCORE,
    TranList,
)
from ofxtools.models.i18n import CURRENCY_CODES, LANG_CODES
from ofxtools.utils import UTC
from ofxtools.Types import DateTime


class TESTTRANLIST(TranList):
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    dataTags = ("TESTAGGREGATE",)


class StatusTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("CODE", "SEVERITY")
    optionalElements = ("MESSAGE",)

    @property
    def root(self):
        root = ET.Element("STATUS")
        ET.SubElement(root, "CODE").text = "0"
        ET.SubElement(root, "SEVERITY").text = "INFO"
        ET.SubElement(root, "MESSAGE").text = "Do your laundry!"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STATUS)
        self.assertEqual(root.code, 0)
        self.assertEqual(root.severity, "INFO")
        self.assertEqual(root.message, "Do your laundry!")

    def testOneOf(self):
        self.oneOfTest("SEVERITY", ("INFO", "WARN", "ERROR"))


class BalTestCase(unittest.TestCase, base.TestAggregate):
    # <BAL> aggregates are mostly optional, so its elements
    # (which are mandatory per the OFX spec) aren't marked as required.
    __test__ = True

    requiredElements = ["NAME", "DESC", "BALTYPE", "VALUE"]
    optionalElements = ["DTASOF", "CURRENCY"]

    @property
    def root(self):
        root = ET.Element("BAL")
        ET.SubElement(root, "NAME").text = "balance"
        ET.SubElement(root, "DESC").text = "Balance"
        ET.SubElement(root, "BALTYPE").text = "DOLLAR"
        ET.SubElement(root, "VALUE").text = "111.22"
        ET.SubElement(root, "DTASOF").text = "20010630"
        currency = test_models_i18n.CurrencyTestCase().root
        root.append(currency)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BAL)
        self.assertEqual(root.name, "balance")
        self.assertEqual(root.desc, "Balance")
        self.assertEqual(root.baltype, "DOLLAR")
        self.assertEqual(root.value, Decimal("111.22"))
        self.assertEqual(root.dtasof, datetime(2001, 6, 30, tzinfo=UTC))
        self.assertIsInstance(root.currency, CURRENCY)

    def testOneOf(self):
        self.oneOfTest("BALTYPE", ("DOLLAR", "PERCENT", "NUMBER"))
        self.oneOfTest("CURSYM", CURRENCY_CODES)


class OfxelementTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = ET.Element("OFXELEMENT")
        ET.SubElement(root, "TAGNAME").text = "ABC.SOMETHING"
        ET.SubElement(root, "NAME").text = "Some OFX extension"
        ET.SubElement(root, "TAGTYPE").text = "A-32"
        ET.SubElement(root, "TAGVALUE").text = "Foobar"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OFXELEMENT)
        self.assertEqual(root.tagname, "ABC.SOMETHING")
        self.assertEqual(root.name, "Some OFX extension")
        self.assertEqual(root.tagtype, "A-32")
        self.assertEqual(root.tagvalue, "Foobar")


class OfxextensionTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    optionalElements = []  # FIXME - how to handle multiple OFXELEMENTs?

    @property
    def root(self):
        root = ET.Element("OFXEXTENSION")
        ofxelement1 = OfxelementTestCase().root
        ofxelement2 = OfxelementTestCase().root
        root.append(ofxelement1)
        root.append(ofxelement2)
        return root

    def testConvert(self):
        # Test OFXEXTENSIONS.  OFXELEMENT is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OFXEXTENSION)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], OFXELEMENT)
        self.assertIsInstance(root[1], OFXELEMENT)


class MsgsetcoreTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "VER",
        "URL",
        "OFXSEC",
        "TRANSPSEC",
        "SIGNONREALM",
        "LANGUAGE",
        "SYNCMODE",
        "RESPFILEER",
    ]
    # optionalElements = ['REFRESHSUPT', 'SPNAME', 'OFXEXTENSION']

    @property
    def root(self):
        root = ET.Element("MSGSETCORE")
        ET.SubElement(root, "VER").text = "1"
        ET.SubElement(root, "URL").text = "https://ofxs.ameritrade.com/cgi-bin/apps/OFX"
        ET.SubElement(root, "OFXSEC").text = "NONE"
        ET.SubElement(root, "TRANSPSEC").text = "Y"
        ET.SubElement(root, "SIGNONREALM").text = "AMERITRADE"
        ET.SubElement(root, "LANGUAGE").text = "ENG"
        ET.SubElement(root, "SYNCMODE").text = "FULL"
        ET.SubElement(root, "REFRESHSUPT").text = "N"
        ET.SubElement(root, "RESPFILEER").text = "N"
        ET.SubElement(root, "INTU.TIMEOUT").text = "360"
        ET.SubElement(root, "SPNAME").text = "Dewey Cheatham & Howe"
        ofxextension = OfxextensionTestCase().root
        root.append(ofxextension)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MSGSETCORE)
        self.assertEqual(root.ver, 1)
        self.assertEqual(root.url, "https://ofxs.ameritrade.com/cgi-bin/apps/OFX")
        self.assertEqual(root.ofxsec, "NONE")
        self.assertEqual(root.transpsec, True)
        self.assertEqual(root.signonrealm, "AMERITRADE")
        self.assertEqual(root.language, "ENG")
        self.assertEqual(root.syncmode, "FULL")
        self.assertEqual(root.refreshsupt, False)
        self.assertEqual(root.respfileer, False)
        self.assertEqual(root.spname, "Dewey Cheatham & Howe")
        self.assertIsInstance(root.ofxextension, OFXEXTENSION)

    def testOneOf(self):
        self.oneOfTest("OFXSEC", ("NONE", "TYPE1"))
        self.oneOfTest("LANGUAGE", LANG_CODES)
        self.oneOfTest("SYNCMODE", ("FULL", "LITE"))


class TranListTestCase(unittest.TestCase):
    @property
    def instance(self):
        subagg0 = TESTSUBAGGREGATE(data="baz")
        agg0 = TESTAGGREGATE(metadata="foo", req00=True, req11=False, testsubaggregate=subagg0)
        subagg1 = TESTSUBAGGREGATE(data="quux")
        agg1 = TESTAGGREGATE(metadata="bar", req01=False, req10=True, testsubaggregate=subagg1)
        dtstart = datetime(2015, 1, 1, tzinfo=UTC)
        dtend = datetime(2015, 3, 31, tzinfo=UTC)
        return TESTTRANLIST(dtstart, dtend, agg0, agg1)

    def testToEtree(self):
        root = self.instance.to_etree()
        self.assertIsInstance(root, ET.Element)
        self.assertEqual(root.tag, "TESTTRANLIST")
        self.assertIsNone(root.text)
        self.assertEqual(len(root), 4)
        dtstart, dtend, agg0, agg1 = root[:]

        self.assertIsInstance(dtstart, ET.Element)
        self.assertEqual(dtstart.tag, "DTSTART")
        self.assertEqual(dtstart.text, "20150101000000")
        self.assertEqual(len(dtstart), 0)

        self.assertIsInstance(dtend, ET.Element)
        self.assertEqual(dtend.tag, "DTEND")
        self.assertEqual(dtend.text, "20150331000000")
        self.assertEqual(len(dtend), 0)

        self.assertIsInstance(agg0, ET.Element)
        self.assertEqual(agg0.tag, "TESTAGGREGATE")
        self.assertIsNone(agg0.text)

        self.assertEqual(len(agg0), 4)
        metadata, req00, req11, subagg = agg0[:]

        self.assertIsInstance(metadata, ET.Element)
        self.assertEqual(metadata.tag, "METADATA")
        self.assertEqual(metadata.text, "foo")
        self.assertEqual(len(metadata), 0)

        self.assertIsInstance(req00, ET.Element)
        self.assertEqual(req00.tag, "REQ00")
        self.assertEqual(req00.text, "Y")
        self.assertEqual(len(req00), 0)

        self.assertIsInstance(req11, ET.Element)
        self.assertEqual(req11.tag, "REQ11")
        self.assertEqual(req11.text, "N")
        self.assertEqual(len(req11), 0)

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, "TESTSUBAGGREGATE")
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, "DATA")
        self.assertEqual(elem.text, "baz")
        self.assertEqual(len(elem), 0)

        self.assertEqual(len(agg1), 4)
        metadata, req00, req11, subagg = agg1[:]

        self.assertIsInstance(metadata, ET.Element)
        self.assertEqual(metadata.tag, "METADATA")
        self.assertEqual(metadata.text, "bar")
        self.assertEqual(len(metadata), 0)

        self.assertIsInstance(req00, ET.Element)
        self.assertEqual(req00.tag, "REQ01")
        self.assertEqual(req00.text, "N")
        self.assertEqual(len(req00), 0)

        self.assertIsInstance(req11, ET.Element)
        self.assertEqual(req11.tag, "REQ10")
        self.assertEqual(req11.text, "Y")
        self.assertEqual(len(req11), 0)

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, "TESTSUBAGGREGATE")
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, "DATA")
        self.assertEqual(elem.text, "quux")
        self.assertEqual(len(elem), 0)

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(
            rep,
            "<TESTTRANLIST dtstart='{}' dtend='{}' len=2>".format(
                datetime(2015, 1, 1, tzinfo=UTC), datetime(2015, 3, 31, tzinfo=UTC)
            ),
        )


if __name__ == "__main__":
    unittest.main()
