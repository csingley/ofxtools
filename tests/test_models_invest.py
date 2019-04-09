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
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.bank.stmt import BALLIST, INV401KSOURCES, INCTRAN
from ofxtools.models.invest import (
    INVPOS,
    POSDEBT,
    POSMF,
    POSOPT,
    POSOTHER,
    POSSTOCK,
    INVTRANLIST,
    INVPOSLIST,
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
    USPRODUCTTYPES,
    INVACCTTYPES,
    INVSUBACCTS,
    INVSTMTMSGSRQV1,
    INVSTMTMSGSRSV1,
)
from ofxtools.models.invest.securities import SECID
from ofxtools.models.i18n import CURRENCY, CURRENCY_CODES
from ofxtools.utils import UTC


# test imports
import base
from test_models_bank_stmt import InctranTestCase, BallistTestCase, StmttrnTestCase
from test_models_securities import SecidTestCase
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

    def testListItems(self):
        # INVPOSLIST may only contain
        # ['POSDEBT', 'POSMF', 'POSOPT', 'POSOTHER', 'POSSTOCK', ]
        listitems = INVPOSLIST.listitems
        self.assertEqual(len(listitems), 5)
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
        #  "INVOOLIST",
        "MKTGINFO",
        #  "INV401KBAL",
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
        #  invoolist = InvoolistTestCase().root
        #  root.append(invoolist)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        # FIXME - INV401K
        #  inv401kbal = Inv401kbalTestCase().root
        #  root.append(inv401kbal)

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
        #  self.assertIsInstance(instance.invoolist, INVOOLIST)
        self.assertEqual(instance.mktginfo, "Get Free Stuff NOW!!")
        #  self.assertIsInstance(instance.inv401kbal, INV401KBAL)

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


if __name__ == "__main__":
    unittest.main()
