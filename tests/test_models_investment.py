# coding: utf-8
""" Unit tests for models.investment """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from decimal import Decimal
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.msgsets import (
    INVSTMTMSGSRQV1,
    INVSTMTMSGSRSV1,
)
from ofxtools.models.bank.stmt import STMTTRN, BALLIST, INV401KSOURCES, INCTRAN
from ofxtools.models.investment import (
    INVTRAN,
    INVBUY,
    INVSELL,
    SECID,
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
    INVPOS,
    POSDEBT,
    POSMF,
    POSOPT,
    POSOTHER,
    POSSTOCK,
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
    INVTRANLIST,
    INVPOSLIST,
    INVOOLIST,
    INCPOS,
    INVACCTFROM,
    INVACCTTO,
    INVACCTINFO,
    INV401KBAL,
    INVBAL,
    INVSTMTRQ,
    INVSTMTRS,
    INVSTMTTRNRQ,
    INVSTMTTRNRS,
    BUYTYPES,
    SELLTYPES,
    OPTBUYTYPES,
    OPTSELLTYPES,
    INCOMETYPES,
    UNITTYPES,
    USPRODUCTTYPES,
    INVACCTTYPES,
    INVSUBACCTS,
)
from ofxtools.models.i18n import CURRENCY, CURRENCY_CODES
from ofxtools.utils import UTC


# test imports
import base
from test_models_bank_stmt import InctranTestCase, BallistTestCase, StmttrnTestCase
from test_models_seclist import SecidTestCase
from test_models_i18n import CurrencyTestCase


class InvacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BROKERID", "ACCTID"]

    @property
    def root(self):
        root = Element("INVACCTFROM")
        SubElement(root, "BROKERID").text = "111000614"
        SubElement(root, "ACCTID").text = "123456789123456789"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVACCTFROM)
        self.assertEqual(instance.brokerid, "111000614")
        self.assertEqual(instance.acctid, "123456789123456789")


class InvaccttoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BROKERID", "ACCTID"]

    @property
    def root(self):
        root = Element("INVACCTTO")
        SubElement(root, "BROKERID").text = "111000614"
        SubElement(root, "ACCTID").text = "123456789123456789"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVACCTTO)
        self.assertEqual(instance.brokerid, "111000614")
        self.assertEqual(instance.acctid, "123456789123456789")


class InvacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVACCTFROM", "USPRODUCTTYPE", "CHECKING", "SVCSTATUS"]
    optionalElements = ["INVACCTTYPE", "OPTIONLEVEL"]

    @property
    def root(self):
        root = Element("INVACCTINFO")
        acctfrom = InvacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, "USPRODUCTTYPE").text = "401K"
        SubElement(root, "CHECKING").text = "Y"
        SubElement(root, "SVCSTATUS").text = "ACTIVE"
        SubElement(root, "INVACCTTYPE").text = "INDIVIDUAL"
        SubElement(root, "OPTIONLEVEL").text = "No way Jose"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVACCTINFO)
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)
        self.assertEqual(instance.usproducttype, "401K")
        self.assertEqual(instance.checking, True)
        self.assertEqual(instance.svcstatus, "ACTIVE")
        self.assertEqual(instance.invaccttype, "INDIVIDUAL")
        self.assertEqual(instance.optionlevel, "No way Jose")

    def testOneOf(self):
        self.oneOfTest("USPRODUCTTYPE", USPRODUCTTYPES)
        self.oneOfTest("SVCSTATUS", SVCSTATUSES)
        self.oneOfTest("INVACCTTYPE", INVACCTTYPES)


class IncposTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INCLUDE"]
    optionalElements = ["DTASOF"]

    @property
    def root(self):
        root = Element("INCPOS")
        SubElement(root, "DTASOF").text = "20091122"
        SubElement(root, "INCLUDE").text = "Y"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INCPOS)
        self.assertEqual(instance.dtasof, datetime(2009, 11, 22, tzinfo=UTC))
        self.assertEqual(instance.include, True)


class InvposlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INVPOSLIST")
        for invpos in ("Posdebt", "Posmf", "Posopt", "Posother", "Posstock"):
            testCase = "{}TestCase".format(invpos)
            elem = globals()[testCase]().root
            root.append(elem)
        return root

    def testdataTags(self):
        # INVPOSLIST may only contain
        # ['POSDEBT', 'POSMF', 'POSOPT', 'POSOTHER', 'POSSTOCK', ]
        allowedTags = INVPOSLIST.dataTags
        self.assertEqual(len(allowedTags), 5)
        root = deepcopy(self.root)
        root.append(StmttrnTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        # Test INVPOSLIST wrapper.  INVPOS members are tested elsewhere.
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVPOSLIST)
        self.assertEqual(len(instance), 5)
        self.assertIsInstance(instance[0], POSDEBT)
        self.assertIsInstance(instance[1], POSMF)
        self.assertIsInstance(instance[2], POSOPT)
        self.assertIsInstance(instance[3], POSOTHER)
        self.assertIsInstance(instance[4], POSSTOCK)


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


class InvbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["AVAILCASH", "MARGINBALANCE", "SHORTBALANCE"]
    optionalElements = ["BUYPOWER"]
    # BALLIST blows up _flatten(); don't test it here

    @property
    def root(self):
        root = Element("INVBAL")
        SubElement(root, "AVAILCASH").text = "12345.67"
        SubElement(root, "MARGINBALANCE").text = "23456.78"
        SubElement(root, "SHORTBALANCE").text = "34567.89"
        SubElement(root, "BUYPOWER").text = "45678.90"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVBAL)
        self.assertEqual(instance.availcash, Decimal("12345.67"))
        self.assertEqual(instance.marginbalance, Decimal("23456.78"))
        self.assertEqual(instance.shortbalance, Decimal("34567.89"))
        self.assertEqual(instance.buypower, Decimal("45678.90"))


class InvtranlistTestCase(unittest.TestCase, base.TranlistTestCase):
    __test__ = True

    @property
    def validSoup(self):
        for root_ in super().validSoup:
            root = deepcopy(root_)
            # 0 contained aggregrates
            yield root
            # Multiple contained aggregates of different types
            for tag in (
                "Invbanktran",
                "Buydebt",
                "Buymf",
                "Buyopt",
                "Buyother",
                "Buystock",
                "Closureopt",
                "Income",
                "Invexpense",
                "Jrnlfund",
                "Jrnlsec",
                "Margininterest",
                "Reinvest",
                "Retofcap",
                "Selldebt",
                "Sellmf",
                "Sellopt",
                "Sellother",
                "Sellstock",
                "Split",
                "Transfer",
            ):
                testcase = "{}TestCase".format(tag)
                invtran = globals()[testcase]
                root.append(invtran().root)
                yield root
                root.append(invtran().root)
                yield root


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


class Inv401kbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("TOTAL",)
    optionalElements = [
        "CASHBAL",
        "PRETAX",
        "AFTERTAX",
        "MATCH",
        "PROFITSHARING",
        "ROLLOVER",
        "OTHERVEST",
        "OTHERNONVEST",
    ]

    @property
    def root(self):
        root = Element("INV401KBAL")
        SubElement(root, "CASHBAL").text = "1"
        SubElement(root, "PRETAX").text = "2"
        SubElement(root, "AFTERTAX").text = "3"
        SubElement(root, "MATCH").text = "4"
        SubElement(root, "PROFITSHARING").text = "5"
        SubElement(root, "ROLLOVER").text = "6"
        SubElement(root, "OTHERVEST").text = "7"
        SubElement(root, "OTHERNONVEST").text = "8"
        SubElement(root, "TOTAL").text = "36"
        ballist = BallistTestCase().root
        root.append(ballist)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INV401KBAL)
        self.assertEqual(instance.cashbal, Decimal("1"))
        self.assertEqual(instance.pretax, Decimal("2"))
        self.assertEqual(instance.aftertax, Decimal("3"))
        self.assertEqual(instance.match, Decimal("4"))
        self.assertEqual(instance.profitsharing, Decimal("5"))
        self.assertEqual(instance.rollover, Decimal("6"))
        self.assertEqual(instance.othervest, Decimal("7"))
        self.assertEqual(instance.othernonvest, Decimal("8"))
        self.assertEqual(instance.total, Decimal("36"))
        self.assertIsInstance(instance.ballist, BALLIST)


class InvposTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = [
        "SECID",
        "HELDINACCT",
        "POSTYPE",
        "UNITS",
        "UNITPRICE",
        "MKTVAL",
        "DTPRICEASOF",
    ]
    optionalElements = ["AVGCOSTBASIS", "CURRENCY", "MEMO", "INV401KSOURCE"]

    @property
    def root(self):
        root = Element("INVPOS")
        secid = SecidTestCase().root
        root.append(secid)
        SubElement(root, "HELDINACCT").text = "MARGIN"
        SubElement(root, "POSTYPE").text = "LONG"
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "UNITPRICE").text = "90"
        SubElement(root, "MKTVAL").text = "9000"
        SubElement(root, "AVGCOSTBASIS").text = "85"
        SubElement(root, "DTPRICEASOF").text = "20130630"
        currency = CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "MEMO").text = "Marked to myth"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.heldinacct, "MARGIN")
        self.assertEqual(instance.postype, "LONG")
        self.assertEqual(instance.units, Decimal("100"))
        self.assertEqual(instance.unitprice, Decimal("90"))
        self.assertEqual(instance.mktval, Decimal("9000"))
        self.assertEqual(instance.avgcostbasis, Decimal("85"))
        self.assertEqual(instance.dtpriceasof, datetime(2013, 6, 30, tzinfo=UTC))
        self.assertEqual(instance.memo, "Marked to myth")
        self.assertEqual(instance.inv401ksource, "PROFITSHARING")
        return instance

    def testOneOf(self):
        self.oneOfTest("HELDINACCT", INVSUBACCTS)
        self.oneOfTest("POSTYPE", ("SHORT", "LONG"))
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)


class PosdebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]

    @property
    def root(self):
        root = Element("POSDEBT")
        invpos = InvposTestCase().root
        root.append(invpos)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, POSDEBT)
        self.assertIsInstance(instance.invpos, INVPOS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        self.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        self.assertEqual(instance.postype, instance.invpos.postype)
        self.assertEqual(instance.units, instance.invpos.units)
        self.assertEqual(instance.unitprice, instance.invpos.unitprice)
        self.assertEqual(instance.mktval, instance.invpos.mktval)
        self.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        self.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        self.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosmfTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["UNITSSTREET", "UNITSUSER", "REINVDIV", "REINVCG"]

    @property
    def root(self):
        root = Element("POSMF")
        invpos = InvposTestCase().root
        root.append(invpos)
        SubElement(root, "UNITSSTREET").text = "200"
        SubElement(root, "UNITSUSER").text = "300"
        SubElement(root, "REINVDIV").text = "N"
        SubElement(root, "REINVCG").text = "Y"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, POSMF)
        self.assertIsInstance(instance.invpos, INVPOS)
        self.assertEqual(instance.unitsstreet, Decimal("200"))
        self.assertEqual(instance.unitsuser, Decimal("300"))
        self.assertEqual(instance.reinvdiv, False)
        self.assertEqual(instance.reinvcg, True)

    def testOneOf(self):
        self.oneOfTest("REINVDIV", ("Y", "N"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        self.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        self.assertEqual(instance.postype, instance.invpos.postype)
        self.assertEqual(instance.units, instance.invpos.units)
        self.assertEqual(instance.unitprice, instance.invpos.unitprice)
        self.assertEqual(instance.mktval, instance.invpos.mktval)
        self.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        self.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        self.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["SECURED"]

    @property
    def root(self):
        root = Element("POSOPT")
        invpos = InvposTestCase().root
        root.append(invpos)
        SubElement(root, "SECURED").text = "COVERED"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, POSOPT)
        self.assertIsInstance(instance.invpos, INVPOS)
        self.assertEqual(instance.secured, "COVERED")

    def testOneOf(self):
        self.oneOfTest("SECURED", ("NAKED", "COVERED"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        self.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        self.assertEqual(instance.postype, instance.invpos.postype)
        self.assertEqual(instance.units, instance.invpos.units)
        self.assertEqual(instance.unitprice, instance.invpos.unitprice)
        self.assertEqual(instance.mktval, instance.invpos.mktval)
        self.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        self.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        self.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosotherTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVPOS"]

    @property
    def root(self):
        root = Element("POSOTHER")
        invpos = InvposTestCase().root
        root.append(invpos)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, POSOTHER)
        self.assertIsInstance(instance.invpos, INVPOS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        self.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        self.assertEqual(instance.postype, instance.invpos.postype)
        self.assertEqual(instance.units, instance.invpos.units)
        self.assertEqual(instance.unitprice, instance.invpos.unitprice)
        self.assertEqual(instance.mktval, instance.invpos.mktval)
        self.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        self.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        self.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["UNITSSTREET", "UNITSUSER", "REINVDIV"]

    @property
    def root(self):
        root = Element("POSSTOCK")
        invpos = InvposTestCase().root
        root.append(invpos)
        SubElement(root, "UNITSSTREET").text = "200"
        SubElement(root, "UNITSUSER").text = "300"
        SubElement(root, "REINVDIV").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, POSSTOCK)
        self.assertIsInstance(instance.invpos, INVPOS)
        self.assertEqual(instance.unitsstreet, Decimal("200"))
        self.assertEqual(instance.unitsuser, Decimal("300"))
        self.assertEqual(instance.reinvdiv, False)

    def testOneOf(self):
        self.oneOfTest("REINVDIV", ("Y", "N"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        self.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        self.assertEqual(instance.postype, instance.invpos.postype)
        self.assertEqual(instance.units, instance.invpos.units)
        self.assertEqual(instance.unitprice, instance.invpos.unitprice)
        self.assertEqual(instance.mktval, instance.invpos.mktval)
        self.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        self.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        self.assertEqual(instance.currate, instance.invpos.currency.currate)


class OoTestCase(unittest.TestCase, base.TestAggregate):
    """ """

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


class InvstmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVACCTFROM", "INCOO", "INCPOS", "INCBAL"]
    optionalElements = ["INCTRAN", "INC401K", "INC401KBAL", "INCTRANIMG"]

    @property
    def root(self):
        root = Element("INVSTMTRQ")
        acctfrom = InvacctfromTestCase().root
        root.append(acctfrom)
        inctran = InctranTestCase().root
        root.append(inctran)
        SubElement(root, "INCOO").text = "N"
        incpos = IncposTestCase().root
        root.append(incpos)
        SubElement(root, "INCBAL").text = "N"
        SubElement(root, "INC401K").text = "Y"
        SubElement(root, "INC401KBAL").text = "N"
        SubElement(root, "INCTRANIMG").text = "Y"

        return root

    def testConvert(self):
        # Test *TRNRQ Aggregate and direct child Elements.
        # Everything below that is tested elsewhere.
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTRQ)
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)
        self.assertIsInstance(instance.inctran, INCTRAN)
        self.assertEqual(instance.incoo, False)
        self.assertIsInstance(instance.incpos, INCPOS)
        self.assertEqual(instance.incbal, False)
        self.assertEqual(instance.inc401k, True)
        self.assertEqual(instance.inc401kbal, False)
        self.assertEqual(instance.inctranimg, True)


class InvstmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTASOF", "CURDEF", "INVACCTFROM"]
    optionalElements = [
        "INVTRANLIST",
        "INVPOSLIST",
        "INVBAL",
        # FIXME - INVOOLIST
        "INVOOLIST",
        "MKTGINFO",
        "INV401KBAL",
    ]
    # 'MKTGINFO', 'INV401KBAL',)
    unsupported = ("INV401K",)

    @property
    def root(self):
        root = Element("INVSTMTRS")
        SubElement(root, "DTASOF").text = "20010530"
        SubElement(root, "CURDEF").text = "USD"
        acctfrom = InvacctfromTestCase().root
        root.append(acctfrom)
        tranlist = InvtranlistTestCase().root
        root.append(tranlist)
        poslist = InvposlistTestCase().root
        root.append(poslist)
        invbal = InvbalTestCase().root
        root.append(invbal)
        # FIXME - INVOOLIST
        invoolist = InvoolistTestCase().root
        root.append(invoolist)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        # FIXME - INV401K
        inv401kbal = Inv401kbalTestCase().root
        root.append(inv401kbal)

        return root

    def testConvert(self):
        # Test **RS Aggregate and direct child Elements.
        # Everything below that is tested elsewhere.
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTRS)
        self.assertEqual(instance.dtasof, datetime(2001, 5, 30, tzinfo=UTC))
        self.assertEqual(instance.curdef, "USD")
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)
        self.assertIsInstance(instance.invtranlist, INVTRANLIST)
        self.assertIsInstance(instance.invposlist, INVPOSLIST)
        self.assertIsInstance(instance.invbal, INVBAL)
        self.assertIsInstance(instance.invoolist, INVOOLIST)
        self.assertEqual(instance.mktginfo, "Get Free Stuff NOW!!")
        self.assertIsInstance(instance.inv401kbal, INV401KBAL)

    def testUnsupported(self):
        root = self.root
        for tag in self.unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIs(instance.account, instance.invacctfrom)
        self.assertIs(instance.balances, instance.invbal)
        self.assertIs(instance.transactions, instance.invtranlist)
        self.assertIs(instance.positions, instance.invposlist)


class InvstmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = InvstmtrqTestCase


class InvstmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = InvstmtrsTestCase

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        stmt = instance.statement
        self.assertIsInstance(stmt, INVSTMTRS)


class Invstmtmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INVSTMTMSGSRQV1")
        for i in range(2):
            stmttrnrq = InvstmttrnrqTestCase().root
            root.append(stmttrnrq)
        return root

    def testdataTags(self):
        # INVSTMTMSGSRQV1 may only contain
        # ["INVSTMTTRNRQ", "INVMAILTRNRQ", "INVMAILSYNCRQ"]
        allowedTags = INVSTMTMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 3)
        root = deepcopy(self.root)
        root.append(InvstmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTMSGSRQV1)
        self.assertEqual(len(instance), 2)
        for stmttrnrs in instance:
            self.assertIsInstance(stmttrnrs, INVSTMTTRNRQ)


class Invstmtmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INVSTMTMSGSRSV1")
        for i in range(2):
            stmttrnrs = InvstmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testdataTags(self):
        # INVSTMTMSGSRSV1 may only contain
        # ["INVSTMTTRNRS", "INVMAILTRNRS", "INVMAILSYNCRS"]
        allowedTags = INVSTMTMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 3)
        root = deepcopy(self.root)
        root.append(InvstmttrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTMSGSRSV1)
        self.assertEqual(len(instance), 2)
        for stmttrnrs in instance:
            self.assertIsInstance(stmttrnrs, INVSTMTTRNRS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIs(instance.statements[0], instance[0].invstmtrs)


if __name__ == "__main__":
    unittest.main()
