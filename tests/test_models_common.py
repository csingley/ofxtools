# coding: utf-8
""" Unit tests for models.common """
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal

import xml.etree.ElementTree as ET


# local imports
from ofxtools.Types import DateTime, ListAggregate
from ofxtools import models
from ofxtools.models.common import BAL, OFXELEMENT, OFXEXTENSION
from ofxtools.models.wrapperbases import TranList
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_i18n as i18n
from test_models_base import TESTAGGREGATE, TESTSUBAGGREGATE


class TESTTRANLIST(TranList):
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)
    testaggregate = ListAggregate(TESTAGGREGATE)


class BalTestCase(unittest.TestCase, base.TestAggregate):
    # <BAL> aggregates are mostly optional, so its elements
    # (which are mandatory per the OFX spec) aren't marked as required.
    __test__ = True

    requiredElements = ["NAME", "DESC", "BALTYPE", "VALUE"]
    optionalElements = ["DTASOF", "CURRENCY"]
    oneOfs = {"BALTYPE": ("DOLLAR", "PERCENT", "NUMBER"), "CURSYM": CURRENCY_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("BAL")
        ET.SubElement(root, "NAME").text = "balance"
        ET.SubElement(root, "DESC").text = "Balance"
        ET.SubElement(root, "BALTYPE").text = "DOLLAR"
        ET.SubElement(root, "VALUE").text = "111.22"
        ET.SubElement(root, "DTASOF").text = "20010630000000.000[+0:UTC]"
        currency = i18n.CurrencyTestCase.etree
        root.append(currency)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BAL(
            name="balance",
            desc="Balance",
            baltype="DOLLAR",
            value=Decimal("111.22"),
            dtasof=datetime(2001, 6, 30, tzinfo=UTC),
            currency=i18n.CurrencyTestCase.aggregate,
        )


class OfxelementTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("OFXELEMENT")
        ET.SubElement(root, "TAGNAME").text = "ABC.SOMETHING"
        ET.SubElement(root, "NAME").text = "Some OFX extension"
        ET.SubElement(root, "TAGTYPE").text = "A-32"
        ET.SubElement(root, "TAGVALUE").text = "Foobar"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return OFXELEMENT(
            tagname="ABC.SOMETHING",
            name="Some OFX extension",
            tagtype="A-32",
            tagvalue="Foobar",
        )


class OfxextensionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("OFXEXTENSION")
        root.append(OfxelementTestCase.etree)
        root.append(OfxelementTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return OFXEXTENSION(OfxelementTestCase.aggregate, OfxelementTestCase.aggregate)


class TranListTestCase(unittest.TestCase, base.TestAggregate):
    @classmethod
    def setUpClass(cls):
        # monkey-patch ofxtools.models so Aggregate.from_etree() picks up
        # our fake OFX aggregates/elements
        models.TESTSUBAGGREGATE = TESTSUBAGGREGATE
        models.TESTAGGREGATE = TESTAGGREGATE
        models.TESTTRANLIST = TESTTRANLIST

    @classmethod
    def tearDownClass(cls):
        # Remove monkey patch
        del models.TESTSUBAGGREGATE
        del models.TESTAGGREGATE
        del models.TESTTRANLIST

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("TESTTRANLIST")
        ET.SubElement(root, "DTSTART").text = "20150101000000.000[+0:UTC]"
        ET.SubElement(root, "DTEND").text = "20150331000000.000[+0:UTC]"

        agg0 = ET.SubElement(root, "TESTAGGREGATE")
        ET.SubElement(agg0, "METADATA").text = "foo"
        ET.SubElement(agg0, "REQ00").text = "Y"
        ET.SubElement(agg0, "REQ11").text = "N"
        subagg0 = ET.SubElement(agg0, "TESTSUBAGGREGATE")
        ET.SubElement(subagg0, "DATA").text = "baz"

        agg1 = ET.SubElement(root, "TESTAGGREGATE")
        ET.SubElement(agg1, "METADATA").text = "bar"
        ET.SubElement(agg1, "REQ01").text = "N"
        ET.SubElement(agg1, "REQ10").text = "Y"
        subagg1 = ET.SubElement(agg1, "TESTSUBAGGREGATE")
        ET.SubElement(subagg1, "DATA").text = "quux"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        subagg0 = TESTSUBAGGREGATE(data="baz")
        agg0 = TESTAGGREGATE(
            metadata="foo", req00=True, req11=False, testsubaggregate=subagg0
        )
        subagg1 = TESTSUBAGGREGATE(data="quux")
        agg1 = TESTAGGREGATE(
            metadata="bar", req01=False, req10=True, testsubaggregate=subagg1
        )
        dtstart = datetime(2015, 1, 1, tzinfo=UTC)
        dtend = datetime(2015, 3, 31, tzinfo=UTC)
        return TESTTRANLIST(agg0, agg1, dtstart=dtstart, dtend=dtend)

    def testRepr(self):
        rep = repr(self.aggregate)
        self.assertEqual(
            rep,
            "<TESTTRANLIST dtstart='{}' dtend='{}' len=2>".format(
                datetime(2015, 1, 1, tzinfo=UTC), datetime(2015, 3, 31, tzinfo=UTC)
            ),
        )


if __name__ == "__main__":
    unittest.main()
