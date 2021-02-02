# coding: utf-8
""" Unit tests for models.invest """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from decimal import Decimal
from datetime import datetime


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.bank.stmt import INV401KSOURCES
from ofxtools.models.invest import (
    BUYTYPES,
    SELLTYPES,
    INCOMETYPES,
    INVSUBACCTS,
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
)
from ofxtools.models.i18n import CURRENCY
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt
import test_models_invest as invest
import test_models_securities as securities
import test_models_i18n as i18n


class InvbanktranTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["STMTTRN", "SUBACCTFUND"]
    oneOfs = {"SUBACCTFUND": INVSUBACCTS}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVBANKTRAN")
        stmttrn = bk_stmt.StmttrnTestCase.etree
        root.append(stmttrn)
        SubElement(root, "SUBACCTFUND").text = "MARGIN"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVBANKTRAN(
            stmttrn=bk_stmt.StmttrnTestCase.aggregate, subacctfund="MARGIN"
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        stmttrn = Aggregate.from_etree(bk_stmt.StmttrnTestCase.etree)
        self.assertEqual(instance.trntype, stmttrn.trntype)
        self.assertEqual(instance.dtposted, stmttrn.dtposted)
        self.assertEqual(instance.trnamt, stmttrn.trnamt)
        self.assertEqual(instance.fitid, stmttrn.fitid)
        self.assertEqual(instance.memo, stmttrn.memo)


class InvtranTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["FITID", "DTTRADE"]
    optionalElements = ["SRVRTID", "DTSETTLE", "REVERSALFITID", "MEMO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVTRAN")
        SubElement(root, "FITID").text = "1001"
        SubElement(root, "SRVRTID").text = "2002"
        SubElement(root, "DTTRADE").text = "20040701000000.000[+0:UTC]"
        SubElement(root, "DTSETTLE").text = "20040704000000.000[+0:UTC]"
        SubElement(root, "REVERSALFITID").text = "3003"
        SubElement(root, "MEMO").text = "Investment Transaction"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVTRAN(
            fitid="1001",
            srvrtid="2002",
            dttrade=datetime(2004, 7, 1, tzinfo=UTC),
            dtsettle=datetime(2004, 7, 4, tzinfo=UTC),
            reversalfitid="3003",
            memo="Investment Transaction",
        )


class InvbuyTestCase(unittest.TestCase, base.TestAggregate):
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
    oneOfs = {
        "SUBACCTSEC": INVSUBACCTS,
        "SUBACCTFUND": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVBUY")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "UNITPRICE").text = "1.50"
        SubElement(root, "MARKUP").text = "0"
        SubElement(root, "COMMISSION").text = "9.99"
        SubElement(root, "TAXES").text = "0"
        SubElement(root, "FEES").text = "1.50"
        SubElement(root, "LOAD").text = "0"
        SubElement(root, "TOTAL").text = "-161.49"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "LOANID").text = "1"
        SubElement(root, "LOANPRINCIPAL").text = "1.50"
        SubElement(root, "LOANINTEREST").text = "3.50"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        SubElement(root, "DTPAYROLL").text = "20040615000000.000[+0:UTC]"
        SubElement(root, "PRIORYEARCONTRIB").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVBUY(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            units=Decimal("100"),
            unitprice=Decimal("1.50"),
            markup=Decimal("0"),
            commission=Decimal("9.99"),
            taxes=Decimal("0"),
            fees=Decimal("1.50"),
            load=Decimal("0"),
            total=Decimal("-161.49"),
            currency=i18n.CurrencyTestCase.aggregate,
            subacctsec="MARGIN",
            subacctfund="CASH",
            loanid="1",
            loanprincipal=Decimal("1.50"),
            loaninterest=Decimal("3.50"),
            inv401ksource="PROFITSHARING",
            dtpayroll=datetime(2004, 6, 15, tzinfo=UTC),
            prioryearcontrib=True,
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)


class InvsellTestCase(unittest.TestCase, base.TestAggregate):
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
    oneOfs = {
        "SUBACCTSEC": INVSUBACCTS,
        "SUBACCTFUND": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSELL")
        invtran = InvtranTestCase.etree
        root.append(invtran)
        secid = securities.SecidTestCase.etree
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
        currency = i18n.CurrencyTestCase.etree
        root.append(currency)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "LOANID").text = "1"
        SubElement(root, "STATEWITHHOLDING").text = "2.50"
        SubElement(root, "PENALTY").text = "0.01"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSELL(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            units=Decimal("-100"),
            unitprice=Decimal("1.50"),
            markdown=Decimal("0"),
            commission=Decimal("9.99"),
            taxes=Decimal("2"),
            fees=Decimal("1.50"),
            load=Decimal("0"),
            withholding=Decimal("3"),
            taxexempt=False,
            total=Decimal("131.00"),
            gain=Decimal("3.47"),
            currency=i18n.CurrencyTestCase.aggregate,
            subacctsec="MARGIN",
            subacctfund="CASH",
            loanid="1",
            statewithholding=Decimal("2.50"),
            penalty=Decimal("0.01"),
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)


class BuydebtTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVBUY"]
    optionalElements = ["ACCRDINT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BUYDEBT")
        invbuy = InvbuyTestCase.etree
        root.append(invbuy)
        SubElement(root, "ACCRDINT").text = "25.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BUYDEBT(invbuy=InvbuyTestCase.aggregate, accrdint=Decimal("25.50"))

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVBUY", "BUYTYPE"]
    optionalElements = ["RELFITID"]
    oneOfs = {"BUYTYPE": BUYTYPES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BUYMF")
        invbuy = InvbuyTestCase.etree
        root.append(invbuy)
        SubElement(root, "BUYTYPE").text = "BUYTOCOVER"
        SubElement(root, "RELFITID").text = "1015"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BUYMF(
            invbuy=InvbuyTestCase.aggregate, buytype="BUYTOCOVER", relfitid="1015"
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVBUY", "OPTBUYTYPE", "SHPERCTRCT"]
    oneOfs = {"OPTBUYTYPE": ("BUYTOOPEN", "BUYTOCLOSE")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BUYOPT")
        invbuy = InvbuyTestCase.etree
        root.append(invbuy)
        SubElement(root, "OPTBUYTYPE").text = "BUYTOCLOSE"
        SubElement(root, "SHPERCTRCT").text = "100"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BUYOPT(
            invbuy=InvbuyTestCase.aggregate, optbuytype="BUYTOCLOSE", shperctrct=100
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVBUY"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BUYOTHER")
        invbuy = InvbuyTestCase.etree
        root.append(invbuy)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BUYOTHER(invbuy=InvbuyTestCase.aggregate)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVBUY", "BUYTYPE"]
    oneOfs = {"BUYTYPE": BUYTYPES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BUYSTOCK")
        root.append(InvbuyTestCase.etree)
        SubElement(root, "BUYTYPE").text = "BUYTOCOVER"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BUYSTOCK(invbuy=InvbuyTestCase.aggregate, buytype="BUYTOCOVER")

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    oneOfs = {"OPTACTION": ("EXERCISE", "ASSIGN", "EXPIRE"), "SUBACCTSEC": INVSUBACCTS}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CLOSUREOPT")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "OPTACTION").text = "EXERCISE"
        SubElement(root, "UNITS").text = "200"
        SubElement(root, "SHPERCTRCT").text = "100"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "RELFITID").text = "1001"
        SubElement(root, "GAIN").text = "123.45"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CLOSUREOPT(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            optaction="EXERCISE",
            units=Decimal("200"),
            shperctrct=100,
            subacctsec="MARGIN",
            relfitid="1001",
            gain=Decimal("123.45"),
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


class IncomeTestCase(unittest.TestCase, base.TestAggregate):
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
    oneOfs = {
        "INCOMETYPE": INCOMETYPES,
        "SUBACCTSEC": INVSUBACCTS,
        "SUBACCTFUND": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INCOME")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "INCOMETYPE").text = "CGLONG"
        SubElement(root, "TOTAL").text = "1500"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "TAXEXEMPT").text = "Y"
        SubElement(root, "WITHHOLDING").text = "123.45"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INCOME(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            incometype="CGLONG",
            total=Decimal("1500"),
            subacctsec="MARGIN",
            subacctfund="CASH",
            taxexempt=True,
            withholding=Decimal("123.45"),
            currency=i18n.CurrencyTestCase.aggregate,
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertIsInstance(instance.currency, CURRENCY)
        self.assertIsNone(instance.origcurrency)
        self.assertEqual(instance.currency.__class__.__name__, "CURRENCY")
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class InvexpenseTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVTRAN", "SECID", "TOTAL", "SUBACCTSEC", "SUBACCTFUND"]
    optionalElements = ["CURRENCY", "INV401KSOURCE"]
    oneOfs = {
        "SUBACCTSEC": INVSUBACCTS,
        "SUBACCTFUND": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVEXPENSE")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "TOTAL").text = "-161.49"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVEXPENSE(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            total=Decimal("-161.49"),
            subacctsec="MARGIN",
            subacctfund="CASH",
            currency=i18n.CurrencyTestCase.aggregate,
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class JrnlfundTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVTRAN", "SUBACCTTO", "SUBACCTFROM", "TOTAL"]
    oneOfs = {"SUBACCTTO": INVSUBACCTS, "SUBACCTFROM": INVSUBACCTS}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("JRNLFUND")
        root.append(InvtranTestCase.etree)
        SubElement(root, "SUBACCTTO").text = "MARGIN"
        SubElement(root, "SUBACCTFROM").text = "CASH"
        SubElement(root, "TOTAL").text = "161.49"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return JRNLFUND(
            invtran=InvtranTestCase.aggregate,
            subacctto="MARGIN",
            subacctfrom="CASH",
            total=Decimal("161.49"),
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)


class JrnlsecTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVTRAN", "SECID", "SUBACCTTO", "SUBACCTFROM", "UNITS"]
    oneOfs = {"SUBACCTTO": INVSUBACCTS, "SUBACCTFROM": INVSUBACCTS}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("JRNLSEC")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "SUBACCTTO").text = "MARGIN"
        SubElement(root, "SUBACCTFROM").text = "CASH"
        SubElement(root, "UNITS").text = "1600"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return JRNLSEC(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            subacctto="MARGIN",
            subacctfrom="CASH",
            units=Decimal("1600"),
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


class MargininterestTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVTRAN", "TOTAL", "SUBACCTFUND"]
    optionalElements = ["CURRENCY"]
    oneOfs = {"SUBACCTFUND": INVSUBACCTS}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MARGININTEREST")
        invtran = InvtranTestCase.etree
        root.append(invtran)
        SubElement(root, "TOTAL").text = "161.49"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        currency = i18n.CurrencyTestCase.etree
        root.append(currency)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MARGININTEREST(
            invtran=InvtranTestCase.aggregate,
            total=Decimal("161.49"),
            subacctfund="CASH",
            currency=i18n.CurrencyTestCase.aggregate,
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class ReinvestTestCase(unittest.TestCase, base.TestAggregate):
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

    oneOfs = {
        "INCOMETYPE": INCOMETYPES,
        "SUBACCTSEC": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("REINVEST")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
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
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return REINVEST(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            total=Decimal("-161.49"),
            incometype="CGLONG",
            subacctsec="MARGIN",
            units=Decimal("100"),
            unitprice=Decimal("1.50"),
            commission=Decimal("9.99"),
            taxes=Decimal("0"),
            fees=Decimal("1.50"),
            load=Decimal("0"),
            taxexempt=True,
            currency=i18n.CurrencyTestCase.aggregate,
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class RetofcapTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVTRAN", "SECID", "TOTAL", "SUBACCTSEC", "SUBACCTFUND"]
    optionalElements = ["CURRENCY", "INV401KSOURCE"]
    oneOfs = {
        "SUBACCTSEC": INVSUBACCTS,
        "SUBACCTFUND": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RETOFCAP")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "TOTAL").text = "-161.49"
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RETOFCAP(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            total=Decimal("-161.49"),
            subacctsec="MARGIN",
            subacctfund="CASH",
            currency=i18n.CurrencyTestCase.aggregate,
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class SelldebtTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVSELL", "SELLREASON"]
    optionalElements = ["ACCRDINT"]

    oneOfs = {"SELLREASON": ("CALL", "SELL", "MATURITY")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SELLDEBT")
        root.append(InvsellTestCase.etree)
        SubElement(root, "SELLREASON").text = "MATURITY"
        SubElement(root, "ACCRDINT").text = "25.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SELLDEBT(
            invsell=InvsellTestCase.aggregate,
            sellreason="MATURITY",
            accrdint=Decimal("25.50"),
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVSELL", "SELLTYPE"]
    optionalElements = ["AVGCOSTBASIS", "RELFITID"]
    oneOfs = {"SELLTYPE": SELLTYPES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SELLMF")
        root.append(InvsellTestCase.etree)
        SubElement(root, "SELLTYPE").text = "SELLSHORT"
        SubElement(root, "AVGCOSTBASIS").text = "2.50"
        SubElement(root, "RELFITID").text = "1015"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SELLMF(
            invsell=InvsellTestCase.aggregate,
            selltype="SELLSHORT",
            avgcostbasis=Decimal("2.50"),
            relfitid="1015",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVSELL", "OPTSELLTYPE", "SHPERCTRCT"]
    optionalElements = ["RELFITID", "RELTYPE", "SECURED"]
    oneOfs = {
        "OPTSELLTYPE": ("SELLTOCLOSE", "SELLTOOPEN"),
        "RELTYPE": ("SPREAD", "STRADDLE", "NONE", "OTHER"),
        "SECURED": ("NAKED", "COVERED"),
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SELLOPT")
        root.append(InvsellTestCase.etree)
        SubElement(root, "OPTSELLTYPE").text = "SELLTOCLOSE"
        SubElement(root, "SHPERCTRCT").text = "100"
        SubElement(root, "RELFITID").text = "1001"
        SubElement(root, "RELTYPE").text = "STRADDLE"
        SubElement(root, "SECURED").text = "NAKED"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SELLOPT(
            invsell=InvsellTestCase.aggregate,
            optselltype="SELLTOCLOSE",
            shperctrct=100,
            relfitid="1001",
            reltype="STRADDLE",
            secured="NAKED",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVSELL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SELLOTHER")
        root.append(InvsellTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SELLOTHER(invsell=InvsellTestCase.aggregate)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    __test__ = True

    requiredElements = ["INVSELL", "SELLTYPE"]
    oneOfs = {"SELLTYPE": SELLTYPES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SELLSTOCK")
        root.append(InvsellTestCase.etree)
        SubElement(root, "SELLTYPE").text = "SELLSHORT"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SELLSTOCK(invsell=InvsellTestCase.aggregate, selltype="SELLSHORT")

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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
    oneOfs = {
        "SUBACCTSEC": INVSUBACCTS,
        "SUBACCTFUND": INVSUBACCTS,
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SPLIT")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "OLDUNITS").text = "200"
        SubElement(root, "NEWUNITS").text = "100"
        SubElement(root, "NUMERATOR").text = "1"
        SubElement(root, "DENOMINATOR").text = "2"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "FRACCASH").text = "0.50"
        SubElement(root, "SUBACCTFUND").text = "CASH"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SPLIT(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            subacctsec="MARGIN",
            oldunits=Decimal("200"),
            newunits=Decimal("100"),
            numerator=Decimal("1"),
            denominator=Decimal("2"),
            currency=i18n.CurrencyTestCase.aggregate,
            fraccash=Decimal("0.50"),
            subacctfund="CASH",
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)


class TransferTestCase(unittest.TestCase, base.TestAggregate):
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
    oneOfs = {
        "SUBACCTSEC": INVSUBACCTS,
        "TFERACTION": ("IN", "OUT"),
        "POSTYPE": ("LONG", "SHORT"),
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("TRANSFER")
        root.append(InvtranTestCase.etree)
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "SUBACCTSEC").text = "MARGIN"
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "TFERACTION").text = "OUT"
        SubElement(root, "POSTYPE").text = "LONG"
        root.append(invest.InvacctfromTestCase.etree)
        SubElement(root, "AVGCOSTBASIS").text = "22.22"
        SubElement(root, "UNITPRICE").text = "23.01"
        SubElement(root, "DTPURCHASE").text = "19991231000000.000[+0:UTC]"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return TRANSFER(
            invtran=InvtranTestCase.aggregate,
            secid=securities.SecidTestCase.aggregate,
            subacctsec="MARGIN",
            units=Decimal("100"),
            tferaction="OUT",
            postype="LONG",
            invacctfrom=invest.InvacctfromTestCase.aggregate,
            avgcostbasis=Decimal("22.22"),
            unitprice=Decimal("23.01"),
            dtpurchase=datetime(1999, 12, 31, tzinfo=UTC),
            inv401ksource="PROFITSHARING",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.fitid, instance.invtran.fitid)
        self.assertEqual(instance.dttrade, instance.invtran.dttrade)
        self.assertEqual(instance.memo, instance.invtran.memo)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


if __name__ == "__main__":
    unittest.main()
