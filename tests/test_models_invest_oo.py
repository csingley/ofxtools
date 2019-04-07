# coding: utf-8
""" Unit tests for models.invest """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from decimal import Decimal
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.bank.stmt import INV401KSOURCES
from ofxtools.models.invest.acct import INVSUBACCTS
from ofxtools.models.invest.transactions import (
    BUYTYPES,
    SELLTYPES,
    OPTBUYTYPES,
    OPTSELLTYPES,
)
from ofxtools.models.invest.openorders import (
    UNITTYPES,
    OO,
    OOBUYDEBT,
    OOBUYMF,
    OOBUYOPT,
    OOBUYOTHER,
    OOBUYSTOCK,
    OOSELLDEBT,
    OOSELLMF,
    OOSELLOPT,
    OOSELLOTHER,
    OOSELLSTOCK,
    SWITCHMF,
    INVOOLIST,
)
from ofxtools.models.invest.securities import SECID
from ofxtools.models.i18n import CURRENCY, CURRENCY_CODES
from ofxtools.utils import UTC


# test imports
import base
from test_models_securities import SecidTestCase
from test_models_bank_stmt import StmttrnTestCase
from test_models_i18n import CurrencyTestCase


class OoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "FITID",
        "SECID",
        "DTPLACED",
        "UNITS",
        "SUBACCT",
        "DURATION",
        "RESTRICTION",
    ]
    optionalElements = [
        "SRVRTID",
        "MINUNITS",
        "LIMITPRICE",
        "STOPPRICE",
        "MEMO",
        "CURRENCY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = Element("OO")
        SubElement(root, "FITID").text = "1001"
        SubElement(root, "SRVRTID").text = "2002"
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "DTPLACED").text = "20040701"
        SubElement(root, "UNITS").text = "150"
        SubElement(root, "SUBACCT").text = "CASH"
        SubElement(root, "DURATION").text = "GOODTILCANCEL"
        SubElement(root, "RESTRICTION").text = "ALLORNONE"
        SubElement(root, "MINUNITS").text = "100"
        SubElement(root, "LIMITPRICE").text = "10.50"
        SubElement(root, "STOPPRICE").text = "10.00"
        SubElement(root, "MEMO").text = "Open Order"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, "1001")
        self.assertEqual(instance.srvrtid, "2002")
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.dtplaced, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(instance.units, Decimal("150"))
        self.assertEqual(instance.subacct, "CASH")
        self.assertEqual(instance.duration, "GOODTILCANCEL")
        self.assertEqual(instance.restriction, "ALLORNONE")
        self.assertEqual(instance.minunits, Decimal("100"))
        self.assertEqual(instance.limitprice, Decimal("10.50"))
        self.assertEqual(instance.stopprice, Decimal("10.00"))
        self.assertEqual(instance.memo, "Open Order")
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCT", INVSUBACCTS)
        self.oneOfTest("DURATION", ("DAY", "GOODTILCANCEL", "IMMEDIATE"))
        self.oneOfTest("RESTRICTION", ("ALLORNONE", "MINUNITS", "NONE"))
        self.oneOfTest("CURSYM", CURRENCY_CODES)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        #  self.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        #  self.assertEqual(instance.postype, instance.invpos.postype)
        #  self.assertEqual(instance.units, instance.invpos.units)
        #  self.assertEqual(instance.unitprice, instance.invpos.unitprice)
        #  self.assertEqual(instance.mktval, instance.invpos.mktval)
        #  self.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class OobuydebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["OO", "AUCTION"]
    optionalElements = ["DTAUCTION"]

    @property
    def root(self):
        root = Element("OOBUYDEBT")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "AUCTION").text = "N"
        SubElement(root, "DTAUCTION").text = "20120109"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.auction, False)
        self.assertEqual(instance.dtauction, datetime(2012, 1, 9, tzinfo=UTC))


class OobuymfTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["OO", "BUYTYPE", "UNITTYPE"]

    @property
    def root(self):
        root = Element("OOBUYMF")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "BUYTYPE").text = "BUY"
        SubElement(root, "UNITTYPE").text = "SHARES"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.buytype, "BUY")
        self.assertEqual(instance.unittype, "SHARES")

    def testOneOf(self):
        self.oneOfTest("BUYTYPE", BUYTYPES)
        self.oneOfTest("UNITTYPE", UNITTYPES)


class OobuyoptTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "OPTBUYTYPE"]

    @property
    def root(self):
        root = Element("OOBUYOPT")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "OPTBUYTYPE").text = "BUYTOOPEN"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.optbuytype, "BUYTOOPEN")

    def testOneOf(self):
        self.oneOfTest("OPTBUYTYPE", OPTBUYTYPES)


class OobuyotherTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "UNITTYPE"]

    @property
    def root(self):
        root = Element("OOBUYOTHER")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "UNITTYPE").text = "SHARES"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.unittype, "SHARES")

    def testOneOf(self):
        self.oneOfTest("UNITTYPE", UNITTYPES)


class OobuystockTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["OO", "BUYTYPE"]

    @property
    def root(self):
        root = Element("OOBUYSTOCK")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "BUYTYPE").text = "BUYTOCOVER"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.buytype, "BUYTOCOVER")

    def testOneOf(self):
        self.oneOfTest("BUYTYPE", BUYTYPES)


class OoselldebtTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO"]
    optionalElements = []

    @property
    def root(self):
        root = Element("OOSELLDEBT")
        oo = OoTestCase().root
        root.append(oo)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)


class OosellmfTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "SELLTYPE", "UNITTYPE", "SELLALL"]
    optionalElements = []

    @property
    def root(self):
        root = Element("OOSELLMF")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "SELLTYPE").text = "SELLSHORT"
        SubElement(root, "UNITTYPE").text = "SHARES"
        SubElement(root, "SELLALL").text = "Y"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.selltype, "SELLSHORT")
        self.assertEqual(instance.unittype, "SHARES")
        self.assertEqual(instance.sellall, True)

    def testOneOf(self):
        self.oneOfTest("SELLTYPE", SELLTYPES)
        self.oneOfTest("UNITTYPE", UNITTYPES)


class OoselloptTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "OPTSELLTYPE"]
    optionalElements = []

    @property
    def root(self):
        root = Element("OOSELLOPT")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "OPTSELLTYPE").text = "SELLTOCLOSE"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.optselltype, "SELLTOCLOSE")

    def testOneOf(self):
        self.oneOfTest("OPTSELLTYPE", OPTSELLTYPES)


class OosellotherTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "UNITTYPE"]
    optionalElements = []

    @property
    def root(self):
        root = Element("OOSELLOTHER")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "UNITTYPE").text = "SHARES"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.unittype, "SHARES")

    def testOneOf(self):
        self.oneOfTest("UNITTYPE", UNITTYPES)


class OosellstockTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "SELLTYPE"]
    optionalElements = []

    @property
    def root(self):
        root = Element("OOSELLSTOCK")
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, "SELLTYPE").text = "SELLSHORT"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertEqual(instance.selltype, "SELLSHORT")

    def testOneOf(self):
        self.oneOfTest("SELLTYPE", SELLTYPES)


class SwitchmfTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["OO", "SECID", "UNITTYPE", "SWITCHALL"]
    optionalElements = []

    @property
    def root(self):
        root = Element("SWITCHMF")
        oo = OoTestCase().root
        root.append(oo)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "UNITTYPE").text = "SHARES"
        SubElement(root, "SWITCHALL").text = "Y"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.oo, OO)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.unittype, "SHARES")
        self.assertEqual(instance.switchall, True)

    def testOneOf(self):
        self.oneOfTest("UNITTYPE", UNITTYPES)


class InvoolistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = []  # FIXME - how to handle OO subclasses?

    @property
    def root(self):
        root = Element("INVOOLIST")
        for oo in (
            "Oobuydebt",
            "Oobuymf",
            "Oobuyopt",
            "Oobuyother",
            "Oobuystock",
            "Ooselldebt",
            "Oosellmf",
            "Oosellopt",
            "Oosellother",
            "Oosellstock",
            "Switchmf",
        ):
            testCase = "{}TestCase".format(oo)
            elem = globals()[testCase]().root
            root.append(elem)
        return root

    def testdataTags(self):
        # INVOOLIST may only contain
        # ['OOBUYDEBT', 'OOBUYMF', 'OOBUYOPT', 'OOBUYOTHER',
        # 'OOBUYSTOCK', 'OOSELLDEBT', 'OOSELLMF', 'OOSELLOPT',
        # 'OOSELLOTHER', 'OOSELLSTOCK', 'SWITCHMF', ]
        allowedTags = INVOOLIST.dataTags
        self.assertEqual(len(allowedTags), 11)
        root = deepcopy(self.root)
        root.append(StmttrnTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        # Test OOLIST wrapper.  OO members are tested elsewhere.
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVOOLIST)
        self.assertEqual(len(instance), 11)
        self.assertIsInstance(instance[0], OOBUYDEBT)
        self.assertIsInstance(instance[1], OOBUYMF)
        self.assertIsInstance(instance[2], OOBUYOPT)
        self.assertIsInstance(instance[3], OOBUYOTHER)
        self.assertIsInstance(instance[4], OOBUYSTOCK)
        self.assertIsInstance(instance[5], OOSELLDEBT)
        self.assertIsInstance(instance[6], OOSELLMF)
        self.assertIsInstance(instance[7], OOSELLOPT)
        self.assertIsInstance(instance[8], OOSELLOTHER)
        self.assertIsInstance(instance[9], OOSELLSTOCK)
        self.assertIsInstance(instance[10], SWITCHMF)


if __name__ == "__main__":
    unittest.main()
