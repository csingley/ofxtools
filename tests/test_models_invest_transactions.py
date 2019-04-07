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
from ofxtools.models.bank.stmt import STMTTRN, INV401KSOURCES
from ofxtools.models.invest import (
    INVTRAN,
    INVBUY,
    INVSELL,
    INVBANKTRAN,
    BUYDEBT,
    BUYMF,
    BUYOPT,
    BUYOTHER,
    BUYSTOCK,
    CLOSUREOPT,
    INCOME,
    INVEXPENSE,
    JRNLFUND,
    JRNLSEC,
    MARGININTEREST,
    REINVEST,
    RETOFCAP,
    SELLDEBT,
    SELLMF,
    SELLOPT,
    SELLOTHER,
    SELLSTOCK,
    SPLIT,
    TRANSFER,
    #  INVTRANLIST,
    INVACCTFROM,
    BUYTYPES,
    SELLTYPES,
    INCOMETYPES,
    INVSUBACCTS,
)
from ofxtools.models.invest.securities import SECID
from ofxtools.models.i18n import CURRENCY
from ofxtools.utils import UTC


# test imports
import base
from test_models_bank_stmt import StmttrnTestCase
from test_models_invest import InvacctfromTestCase
from test_models_securities import SecidTestCase
from test_models_i18n import CurrencyTestCase


class InvbanktranTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["STMTTRN", "SUBACCTFUND"]

    @property
    def root(self):
        root = Element("INVBANKTRAN")
        stmttrn = StmttrnTestCase().root
        root.append(stmttrn)
        SubElement(root, "SUBACCTFUND").text = "MARGIN"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVBANKTRAN)
        self.assertIsInstance(instance.stmttrn, STMTTRN)
        self.assertEqual(instance.subacctfund, "MARGIN")

    def testOneOf(self):
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        stmttrn = Aggregate.from_etree(StmttrnTestCase().root)
        self.assertEqual(instance.trntype, stmttrn.trntype)
        self.assertEqual(instance.dtposted, stmttrn.dtposted)
        self.assertEqual(instance.trnamt, stmttrn.trnamt)
        self.assertEqual(instance.fitid, stmttrn.fitid)
        self.assertEqual(instance.memo, stmttrn.memo)


class InvtranTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["FITID", "DTTRADE"]
    optionalElements = ["SRVRTID", "DTSETTLE", "REVERSALFITID", "MEMO"]

    @property
    def root(self):
        root = Element("INVTRAN")
        SubElement(root, "FITID").text = "1001"
        SubElement(root, "SRVRTID").text = "2002"
        SubElement(root, "DTTRADE").text = "20040701"
        SubElement(root, "DTSETTLE").text = "20040704"
        SubElement(root, "REVERSALFITID").text = "3003"
        SubElement(root, "MEMO").text = "Investment Transaction"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, "1001")
        self.assertEqual(instance.srvrtid, "2002")
        self.assertEqual(instance.dttrade, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(instance.dtsettle, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(instance.reversalfitid, "3003")
        self.assertEqual(instance.memo, "Investment Transaction")
        return instance


class InvbuyTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "UNITS",
        "UNITPRICE",
        "TOTAL",
        "SUBACCTSEC",
        "SUBACCTFUND",
    ]
    optionalElements = [
        "MARKUP",
        "COMMISSION",
        "TAXES",
        "FEES",
        "LOAD",
        "CURRENCY",
        "LOANID",
        "LOANPRINCIPAL",
        "LOANINTEREST",
        "INV401KSOURCE",
        "DTPAYROLL",
        "PRIORYEARCONTRIB",
    ]

    @property
    def root(self):
        root = Element("INVBUY")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "UNITPRICE").text = "1.50"
        SubElement(root, "MARKUP").text = "0"
        SubElement(root, "COMMISSION").text = "9.99"
        SubElement(root, "TAXES").text = "0"
        SubElement(root, "FEES").text = "1.50"
        SubElement(root, "LOAD").text = "0"
        SubElement(root, "TOTAL").text = "-161.49"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "LOANID").text = "1"
        SubElement(root, "LOANPRINCIPAL").text = "1.50"
        SubElement(root, "LOANINTEREST").text = "3.50"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        SubElement(root, "DTPAYROLL").text = "20040615"
        SubElement(root, "PRIORYEARCONTRIB").text = "Y"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.units, Decimal("100"))
        self.assertEqual(instance.unitprice, Decimal("1.50"))
        self.assertEqual(instance.markup, Decimal("0"))
        self.assertEqual(instance.commission, Decimal("9.99"))
        self.assertEqual(instance.taxes, Decimal("0"))
        self.assertEqual(instance.fees, Decimal("1.50"))
        self.assertEqual(instance.load, Decimal("0"))
        self.assertEqual(instance.total, Decimal("-161.49"))
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertEqual(instance.loanid, "1")
        self.assertEqual(instance.loanprincipal, Decimal("1.50"))
        self.assertEqual(instance.loaninterest, Decimal("3.50"))
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        self.assertEqual(instance.dtpayroll, datetime(2004, 6, 15, tzinfo=UTC))
        self.assertEqual(instance.prioryearcontrib, True)
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)


class InvsellTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "UNITS",
        "UNITPRICE",
        "TOTAL",
        "SUBACCTSEC",
        "SUBACCTFUND",
    ]
    optionalElements = [
        "MARKDOWN",
        "COMMISSION",
        "TAXES",
        "FEES",
        "LOAD",
        "WITHHOLDING",
        "TAXEXEMPT",
        "GAIN",
        "CURRENCY",
        "LOANID",
        "STATEWITHHOLDING",
        "PENALTY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = Element("INVSELL")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "UNITS").text = "-100"
        SubElement(root, "UNITPRICE").text = "1.50"
        SubElement(root, "MARKDOWN").text = "0"
        SubElement(root, "COMMISSION").text = "9.99"
        SubElement(root, "TAXES").text = "2"
        SubElement(root, "FEES").text = "1.50"
        SubElement(root, "LOAD").text = "0"
        SubElement(root, "WITHHOLDING").text = "3"
        SubElement(root, "TAXEXEMPT").text = "N"
        SubElement(root, "TOTAL").text = "131.00"
        SubElement(root, "GAIN").text = "3.47"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "LOANID").text = "1"
        SubElement(root, "STATEWITHHOLDING").text = "2.50"
        SubElement(root, "PENALTY").text = "0.01"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.units, Decimal("-100"))
        self.assertEqual(instance.unitprice, Decimal("1.50"))
        self.assertEqual(instance.markdown, Decimal("0"))
        self.assertEqual(instance.commission, Decimal("9.99"))
        self.assertEqual(instance.taxes, Decimal("2"))
        self.assertEqual(instance.fees, Decimal("1.50"))
        self.assertEqual(instance.load, Decimal("0"))
        self.assertEqual(instance.withholding, Decimal("3"))
        self.assertEqual(instance.taxexempt, False)
        self.assertEqual(instance.total, Decimal("131"))
        self.assertEqual(instance.gain, Decimal("3.47"))
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertEqual(instance.loanid, "1")
        self.assertEqual(instance.statewithholding, Decimal("2.50"))
        self.assertEqual(instance.penalty, Decimal("0.01"))
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)


class BuydebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVBUY"]
    optionalElements = ["ACCRDINT"]

    @property
    def root(self):
        root = Element("BUYDEBT")
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, "ACCRDINT").text = "25.50"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BUYDEBT)
        self.assertIsInstance(instance.invbuy, INVBUY)
        self.assertEqual(instance.accrdint, Decimal("25.50"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invbuy.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invbuy.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invbuy.units)
        self.assertEqual(instance.unitprice, instance.invbuy.unitprice)
        self.assertEqual(instance.total, instance.invbuy.total)
        self.assertEqual(instance.curtype, instance.invbuy.curtype)
        self.assertEqual(instance.cursym, instance.invbuy.cursym)
        self.assertEqual(instance.currate, instance.invbuy.currate)
        self.assertEqual(instance.subacctsec, instance.invbuy.subacctsec)
        self.assertEqual(instance.fitid, instance.invbuy.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invbuy.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invbuy.invtran.memo)


class BuymfTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVBUY", "BUYTYPE"]
    optionalElements = ["RELFITID"]

    @property
    def root(self):
        root = Element("BUYMF")
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, "BUYTYPE").text = "BUYTOCOVER"
        SubElement(root, "RELFITID").text = "1015"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BUYMF)
        self.assertIsInstance(instance.invbuy, INVBUY)
        self.assertEqual(instance.buytype, "BUYTOCOVER")
        self.assertEqual(instance.relfitid, "1015")

    def testOneOf(self):
        self.oneOfTest("BUYTYPE", BUYTYPES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invbuy.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invbuy.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invbuy.units)
        self.assertEqual(instance.unitprice, instance.invbuy.unitprice)
        self.assertEqual(instance.total, instance.invbuy.total)
        self.assertEqual(instance.curtype, instance.invbuy.curtype)
        self.assertEqual(instance.cursym, instance.invbuy.cursym)
        self.assertEqual(instance.currate, instance.invbuy.currate)
        self.assertEqual(instance.subacctsec, instance.invbuy.subacctsec)
        self.assertEqual(instance.fitid, instance.invbuy.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invbuy.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invbuy.invtran.memo)


class BuyoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVBUY", "OPTBUYTYPE", "SHPERCTRCT"]

    @property
    def root(self):
        root = Element("BUYOPT")
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, "OPTBUYTYPE").text = "BUYTOCLOSE"
        SubElement(root, "SHPERCTRCT").text = "100"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BUYOPT)
        self.assertIsInstance(instance.invbuy, INVBUY)
        self.assertEqual(instance.optbuytype, "BUYTOCLOSE")
        self.assertEqual(instance.shperctrct, 100)

    def testOneOf(self):
        self.oneOfTest("OPTBUYTYPE", ("BUYTOOPEN", "BUYTOCLOSE"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invbuy.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invbuy.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invbuy.units)
        self.assertEqual(instance.unitprice, instance.invbuy.unitprice)
        self.assertEqual(instance.total, instance.invbuy.total)
        self.assertEqual(instance.curtype, instance.invbuy.curtype)
        self.assertEqual(instance.cursym, instance.invbuy.cursym)
        self.assertEqual(instance.currate, instance.invbuy.currate)
        self.assertEqual(instance.subacctsec, instance.invbuy.subacctsec)
        self.assertEqual(instance.fitid, instance.invbuy.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invbuy.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invbuy.invtran.memo)


class BuyotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVBUY"]

    @property
    def root(self):
        root = Element("BUYOTHER")
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BUYOTHER)
        self.assertIsInstance(instance.invbuy, INVBUY)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invbuy.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invbuy.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invbuy.units)
        self.assertEqual(instance.unitprice, instance.invbuy.unitprice)
        self.assertEqual(instance.total, instance.invbuy.total)
        self.assertEqual(instance.curtype, instance.invbuy.curtype)
        self.assertEqual(instance.cursym, instance.invbuy.cursym)
        self.assertEqual(instance.currate, instance.invbuy.currate)
        self.assertEqual(instance.subacctsec, instance.invbuy.subacctsec)
        self.assertEqual(instance.fitid, instance.invbuy.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invbuy.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invbuy.invtran.memo)


class BuystockTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVBUY", "BUYTYPE"]

    @property
    def root(self):
        root = Element("BUYSTOCK")
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, "BUYTYPE").text = "BUYTOCOVER"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BUYSTOCK)
        self.assertIsInstance(instance.invbuy, INVBUY)
        self.assertEqual(instance.buytype, "BUYTOCOVER")

    def testOneOf(self):
        self.oneOfTest("BUYTYPE", BUYTYPES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invbuy.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invbuy.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invbuy.units)
        self.assertEqual(instance.unitprice, instance.invbuy.unitprice)
        self.assertEqual(instance.total, instance.invbuy.total)
        self.assertEqual(instance.curtype, instance.invbuy.curtype)
        self.assertEqual(instance.cursym, instance.invbuy.cursym)
        self.assertEqual(instance.currate, instance.invbuy.currate)
        self.assertEqual(instance.subacctsec, instance.invbuy.subacctsec)
        self.assertEqual(instance.fitid, instance.invbuy.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invbuy.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invbuy.invtran.memo)


class ClosureoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "OPTACTION",
        "UNITS",
        "SHPERCTRCT",
        "SUBACCTSEC",
    ]
    optionalElements = ["RELFITID", "GAIN"]

    @property
    def root(self):
        root = Element("CLOSUREOPT")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "OPTACTION").text = "EXERCISE"
        SubElement(root, "UNITS").text = "200"
        SubElement(root, "SHPERCTRCT").text = "100"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "RELFITID").text = "1001"
        SubElement(root, "GAIN").text = "123.45"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CLOSUREOPT)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.optaction, "EXERCISE")
        self.assertEqual(instance.units, Decimal("200"))
        self.assertEqual(instance.shperctrct, 100)
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.relfitid, "1001")
        self.assertEqual(instance.gain, Decimal("123.45"))
        return instance

    def testOneOf(self):
        self.oneOfTest("OPTACTION", ("EXERCISE", "ASSIGN", "EXPIRE"))
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


class IncomeTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "INCOMETYPE",
        "TOTAL",
        "SUBACCTSEC",
        "SUBACCTFUND",
    ]
    optionalElements = ["TAXEXEMPT", "WITHHOLDING", "CURRENCY", "INV401KSOURCE"]

    @property
    def root(self):
        root = Element("INCOME")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "INCOMETYPE").text = "CGLONG"
        SubElement(root, "TOTAL").text = "1500"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "TAXEXEMPT").text = "Y"
        SubElement(root, "WITHHOLDING").text = "123.45"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INCOME)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.incometype, "CGLONG")
        self.assertEqual(instance.total, Decimal("1500"))
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertEqual(instance.taxexempt, True)
        self.assertEqual(instance.withholding, Decimal("123.45"))
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("INCOMETYPE", INCOMETYPES)
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class InvexpenseTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVTRAN", "SECID", "TOTAL", "SUBACCTSEC", "SUBACCTFUND"]
    optionalElements = ["CURRENCY", "INV401KSOURCE"]

    @property
    def root(self):
        root = Element("INVEXPENSE")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "TOTAL").text = "-161.49"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVEXPENSE)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.total, Decimal("-161.49"))
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")

    def testOneOf(self):
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class JrnlfundTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVTRAN", "SUBACCTTO", "SUBACCTFROM", "TOTAL"]

    @property
    def root(self):
        root = Element("JRNLFUND")
        invtran = InvtranTestCase().root
        root.append(invtran)
        SubElement(root, "SUBACCTTO").text = "MARGIN"
        SubElement(root, "SUBACCTFROM").text = "CASH"
        SubElement(root, "TOTAL").text = "161.49"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, JRNLFUND)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertEqual(instance.subacctto, "MARGIN")
        self.assertEqual(instance.subacctfrom, "CASH")
        self.assertEqual(instance.total, Decimal("161.49"))

    def testOneOf(self):
        self.oneOfTest("SUBACCTTO", INVSUBACCTS)
        self.oneOfTest("SUBACCTFROM", INVSUBACCTS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)


class JrnlsecTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVTRAN", "SECID", "SUBACCTTO", "SUBACCTFROM", "UNITS"]

    @property
    def root(self):
        root = Element("JRNLSEC")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "SUBACCTTO").text = "MARGIN"
        SubElement(root, "SUBACCTFROM").text = "CASH"
        SubElement(root, "UNITS").text = "1600"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, JRNLSEC)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.subacctto, "MARGIN")
        self.assertEqual(instance.subacctfrom, "CASH")
        self.assertEqual(instance.units, Decimal("1600"))

    def testOneOf(self):
        self.oneOfTest("SUBACCTTO", INVSUBACCTS)
        self.oneOfTest("SUBACCTFROM", INVSUBACCTS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


class MargininterestTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVTRAN", "TOTAL", "SUBACCTFUND"]
    optionalElements = ["CURRENCY"]

    @property
    def root(self):
        root = Element("MARGININTEREST")
        invtran = InvtranTestCase().root
        root.append(invtran)
        SubElement(root, "TOTAL").text = "161.49"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        currency = CurrencyTestCase().root
        root.append(currency)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, MARGININTEREST)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertEqual(instance.total, Decimal("161.49"))
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertIsInstance(instance.currency, CURRENCY)
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class ReinvestTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "INCOMETYPE",
        "TOTAL",
        "SUBACCTSEC",
        "UNITS",
        "UNITPRICE",
    ]
    optionalElements = [
        "COMMISSION",
        "TAXES",
        "FEES",
        "LOAD",
        "TAXEXEMPT",
        "CURRENCY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = Element("REINVEST")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "INCOMETYPE").text = "CGLONG"
        SubElement(root, "TOTAL").text = "-161.49"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "UNITPRICE").text = "1.50"
        SubElement(root, "COMMISSION").text = "9.99"
        SubElement(root, "TAXES").text = "0"
        SubElement(root, "FEES").text = "1.50"
        SubElement(root, "LOAD").text = "0"
        SubElement(root, "TAXEXEMPT").text = "Y"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, REINVEST)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.total, Decimal("-161.49"))
        self.assertEqual(instance.incometype, "CGLONG")
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.units, Decimal("100"))
        self.assertEqual(instance.unitprice, Decimal("1.50"))
        self.assertEqual(instance.commission, Decimal("9.99"))
        self.assertEqual(instance.taxes, Decimal("0"))
        self.assertEqual(instance.fees, Decimal("1.50"))
        self.assertEqual(instance.load, Decimal("0"))
        self.assertEqual(instance.taxexempt, True)
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("INCOMETYPE", INCOMETYPES)
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class RetofcapTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVTRAN", "SECID", "TOTAL", "SUBACCTSEC", "SUBACCTFUND"]
    optionalElements = ["CURRENCY", "INV401KSOURCE"]

    @property
    def root(self):
        root = Element("RETOFCAP")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "TOTAL").text = "-161.49"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RETOFCAP)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.total, Decimal("-161.49"))
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class SelldebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVSELL", "SELLREASON"]
    optionalElements = ["ACCRDINT"]

    @property
    def root(self):
        root = Element("SELLDEBT")
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, "SELLREASON").text = "MATURITY"
        SubElement(root, "ACCRDINT").text = "25.50"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SELLDEBT)
        self.assertIsInstance(instance.invsell, INVSELL)
        self.assertEqual(instance.sellreason, "MATURITY")
        self.assertEqual(instance.accrdint, Decimal("25.50"))

    def testOneOf(self):
        self.oneOfTest("SELLREASON", ("CALL", "SELL", "MATURITY"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invsell.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invsell.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invsell.units)
        self.assertEqual(instance.unitprice, instance.invsell.unitprice)
        self.assertEqual(instance.total, instance.invsell.total)
        self.assertEqual(instance.curtype, instance.invsell.curtype)
        self.assertEqual(instance.cursym, instance.invsell.cursym)
        self.assertEqual(instance.currate, instance.invsell.currate)
        self.assertEqual(instance.subacctsec, instance.invsell.subacctsec)
        self.assertEqual(instance.fitid, instance.invsell.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invsell.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invsell.invtran.memo)


class SellmfTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVSELL", "SELLTYPE"]
    optionalElements = ["AVGCOSTBASIS", "RELFITID"]

    @property
    def root(self):
        root = Element("SELLMF")
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, "SELLTYPE").text = "SELLSHORT"
        SubElement(root, "AVGCOSTBASIS").text = "2.50"
        SubElement(root, "RELFITID").text = "1015"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SELLMF)
        self.assertIsInstance(instance.invsell, INVSELL)
        self.assertEqual(instance.selltype, "SELLSHORT")
        self.assertEqual(instance.relfitid, "1015")

    def testOneOf(self):
        self.oneOfTest("SELLTYPE", SELLTYPES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invsell.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invsell.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invsell.units)
        self.assertEqual(instance.unitprice, instance.invsell.unitprice)
        self.assertEqual(instance.total, instance.invsell.total)
        self.assertEqual(instance.curtype, instance.invsell.curtype)
        self.assertEqual(instance.cursym, instance.invsell.cursym)
        self.assertEqual(instance.currate, instance.invsell.currate)
        self.assertEqual(instance.subacctsec, instance.invsell.subacctsec)
        self.assertEqual(instance.fitid, instance.invsell.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invsell.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invsell.invtran.memo)


class SelloptTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVSELL", "OPTSELLTYPE", "SHPERCTRCT"]
    optionalElements = ["RELFITID", "RELTYPE", "SECURED"]

    @property
    def root(self):
        root = Element("SELLOPT")
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, "OPTSELLTYPE").text = "SELLTOCLOSE"
        SubElement(root, "SHPERCTRCT").text = "100"
        SubElement(root, "RELFITID").text = "1001"
        SubElement(root, "RELTYPE").text = "STRADDLE"
        SubElement(root, "SECURED").text = "NAKED"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SELLOPT)
        self.assertIsInstance(instance.invsell, INVSELL)
        self.assertEqual(instance.optselltype, "SELLTOCLOSE")
        self.assertEqual(instance.shperctrct, 100)
        self.assertEqual(instance.relfitid, "1001")
        self.assertEqual(instance.reltype, "STRADDLE")
        self.assertEqual(instance.secured, "NAKED")

    def testOneOf(self):
        self.oneOfTest("OPTSELLTYPE", ("SELLTOCLOSE", "SELLTOOPEN"))
        self.oneOfTest("RELTYPE", ("SPREAD", "STRADDLE", "NONE", "OTHER"))
        self.oneOfTest("SECURED", ("NAKED", "COVERED"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invsell.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invsell.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invsell.units)
        self.assertEqual(instance.unitprice, instance.invsell.unitprice)
        self.assertEqual(instance.total, instance.invsell.total)
        self.assertEqual(instance.curtype, instance.invsell.curtype)
        self.assertEqual(instance.cursym, instance.invsell.cursym)
        self.assertEqual(instance.currate, instance.invsell.currate)
        self.assertEqual(instance.subacctsec, instance.invsell.subacctsec)
        self.assertEqual(instance.fitid, instance.invsell.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invsell.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invsell.invtran.memo)


class SellotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVSELL"]

    @property
    def root(self):
        root = Element("SELLOTHER")
        invsell = InvsellTestCase().root
        root.append(invsell)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SELLOTHER)
        self.assertIsInstance(instance.invsell, INVSELL)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invsell.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invsell.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invsell.units)
        self.assertEqual(instance.unitprice, instance.invsell.unitprice)
        self.assertEqual(instance.total, instance.invsell.total)
        self.assertEqual(instance.curtype, instance.invsell.curtype)
        self.assertEqual(instance.cursym, instance.invsell.cursym)
        self.assertEqual(instance.currate, instance.invsell.currate)
        self.assertEqual(instance.subacctsec, instance.invsell.subacctsec)
        self.assertEqual(instance.fitid, instance.invsell.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invsell.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invsell.invtran.memo)


class SellstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVSELL", "SELLTYPE"]

    @property
    def root(self):
        root = Element("SELLSTOCK")
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, "SELLTYPE").text = "SELLSHORT"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SELLSTOCK)
        self.assertIsInstance(instance.invsell, INVSELL)
        self.assertEqual(instance.selltype, "SELLSHORT")

    def testOneOf(self):
        self.oneOfTest("SELLTYPE", SELLTYPES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invsell.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invsell.secid.uniqueidtype)
        self.assertEqual(instance.units, instance.invsell.units)
        self.assertEqual(instance.unitprice, instance.invsell.unitprice)
        self.assertEqual(instance.total, instance.invsell.total)
        self.assertEqual(instance.curtype, instance.invsell.curtype)
        self.assertEqual(instance.cursym, instance.invsell.cursym)
        self.assertEqual(instance.currate, instance.invsell.currate)
        self.assertEqual(instance.subacctsec, instance.invsell.subacctsec)
        self.assertEqual(instance.fitid, instance.invsell.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invsell.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invsell.invtran.memo)


class SplitTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "SUBACCTSEC",
        "OLDUNITS",
        "NEWUNITS",
        "NUMERATOR",
        "DENOMINATOR",
    ]
    optionalElements = ["CURRENCY", "FRACCASH", "SUBACCTFUND", "INV401KSOURCE"]

    @property
    def root(self):
        root = Element("SPLIT")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "OLDUNITS").text = "200"
        SubElement(root, "NEWUNITS").text = "100"
        SubElement(root, "NUMERATOR").text = "1"
        SubElement(root, "DENOMINATOR").text = "2"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "FRACCASH").text = "0.50"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SPLIT)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.oldunits, Decimal("200"))
        self.assertEqual(instance.newunits, Decimal("100"))
        self.assertEqual(instance.numerator, Decimal("1"))
        self.assertEqual(instance.denominator, Decimal("2"))
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertEqual(instance.fraccash, Decimal("0.50"))
        self.assertEqual(instance.subacctfund, "CASH")
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("SUBACCTFUND", INVSUBACCTS)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class TransferTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "INVTRAN",
        "SECID",
        "SUBACCTSEC",
        "UNITS",
        "TFERACTION",
        "POSTYPE",
    ]
    optionalElements = [
        "INVACCTFROM",
        "AVGCOSTBASIS",
        "UNITPRICE",
        "DTPURCHASE",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = Element("TRANSFER")
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "TFERACTION").text = "OUT"
        SubElement(root, "POSTYPE").text = "LONG"
        invacctfrom = InvacctfromTestCase().root
        root.append(invacctfrom)
        SubElement(root, "AVGCOSTBASIS").text = "22.22"
        SubElement(root, "UNITPRICE").text = "23.01"
        SubElement(root, "DTPURCHASE").text = "19991231"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, TRANSFER)
        self.assertIsInstance(instance.invtran, INVTRAN)
        self.assertIsInstance(instance.secid, SECID)
        self.assertEqual(instance.subacctsec, "MARGIN")
        self.assertEqual(instance.units, Decimal("100"))
        self.assertEqual(instance.tferaction, "OUT")
        self.assertEqual(instance.postype, "LONG")
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)
        self.assertEqual(instance.avgcostbasis, Decimal("22.22"))
        self.assertEqual(instance.unitprice, Decimal("23.01"))
        self.assertEqual(instance.dtpurchase, datetime(1999, 12, 31, tzinfo=UTC))
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("SUBACCTSEC", INVSUBACCTS)
        self.oneOfTest("TFERACTION", ("IN", "OUT"))
        self.oneOfTest("POSTYPE", ("LONG", "SHORT"))
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


if __name__ == "__main__":
    unittest.main()
