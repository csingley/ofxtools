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
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_bank_stmt import InctranTestCase, BallistTestCase, StmttrnTestCase
from test_models_securities import SecidTestCase
from test_models_i18n import CurrencyTestCase
#  from test_models_invest_transactions import InvbanktranTestCase


class InvacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BROKERID", "ACCTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVACCTFROM")
        SubElement(root, "BROKERID").text = "111000614"
        SubElement(root, "ACCTID").text = "123456789123456789"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVACCTFROM(brokerid="111000614", acctid="123456789123456789")


class InvaccttoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BROKERID", "ACCTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVACCTTO")
        SubElement(root, "BROKERID").text = "111000614"
        SubElement(root, "ACCTID").text = "123456789123456789"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVACCTTO(brokerid="111000614", acctid="123456789123456789")


class InvacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVACCTFROM", "USPRODUCTTYPE", "CHECKING", "SVCSTATUS"]
    optionalElements = ["INVACCTTYPE", "OPTIONLEVEL"]
    oneOfs = {"USPRODUCTTYPE": USPRODUCTTYPES, "SVCSTATUS": SVCSTATUSES,
              "INVACCTTYPE": INVACCTTYPES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVACCTINFO")
        acctfrom = InvacctfromTestCase.etree
        root.append(acctfrom)
        SubElement(root, "USPRODUCTTYPE").text = "401K"
        SubElement(root, "CHECKING").text = "Y"
        SubElement(root, "SVCSTATUS").text = "ACTIVE"
        SubElement(root, "INVACCTTYPE").text = "INDIVIDUAL"
        SubElement(root, "OPTIONLEVEL").text = "No way Jose"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVACCTINFO(invacctfrom=InvacctfromTestCase.aggregate,
                           usproducttype="401K", checking=True,
                           svcstatus="ACTIVE", invaccttype="INDIVIDUAL",
                           optionlevel="No way Jose")


class IncposTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INCLUDE"]
    optionalElements = ["DTASOF"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INCPOS")
        SubElement(root, "DTASOF").text = "20091122000000.000[0:GMT]"
        SubElement(root, "INCLUDE").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INCPOS(dtasof=datetime(2009, 11, 22, tzinfo=UTC), include=True)


class InvposlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVPOSLIST")
        for invpos in ("Posdebt", "Posmf", "Posopt", "Posother", "Posstock"):
            testCase = "{}TestCase".format(invpos)
            elem = globals()[testCase].etree
            root.append(elem)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVPOSLIST(PosdebtTestCase.aggregate, PosmfTestCase.aggregate,
                          PosoptTestCase.aggregate, PosotherTestCase.aggregate,
                          PosstockTestCase.aggregate)

    def testListItems(cls):
        # INVPOSLIST may only contain
        # ['POSDEBT', 'POSMF', 'POSOPT', 'POSOTHER', 'POSSTOCK', ]
        listitems = INVPOSLIST.listitems
        cls.assertEqual(len(listitems), 5)
        root = cls.etree
        root.append(StmttrnTestCase.etree)

        with cls.assertRaises(ValueError):
            Aggregate.from_etree(root)


class InvbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["AVAILCASH", "MARGINBALANCE", "SHORTBALANCE"]
    optionalElements = ["BUYPOWER"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVBAL")
        SubElement(root, "AVAILCASH").text = "12345.67"
        SubElement(root, "MARGINBALANCE").text = "23456.78"
        SubElement(root, "SHORTBALANCE").text = "34567.89"
        SubElement(root, "BUYPOWER").text = "45678.90"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVBAL(availcash=Decimal("12345.67"),
                      marginbalance=Decimal("23456.78"),
                      shortbalance=Decimal("34567.89"),
                      buypower=Decimal("45678.90"))


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

    @classproperty
    @classmethod
    def etree(cls):
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
        ballist = BallistTestCase.etree
        root.append(ballist)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INV401KBAL(cashbal=Decimal("1"), pretax=Decimal("2"),
                          aftertax=Decimal("3"), match=Decimal("4"),
                          profitsharing=Decimal("5"), rollover=Decimal("6"),
                          othervest=Decimal("7"), othernonvest=Decimal("8"),
                          total=Decimal("36"),
                          ballist=BallistTestCase.aggregate)


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
    oneOfs = {"HELDINACCT": INVSUBACCTS, "POSTYPE": ("SHORT", "LONG"),
              "INV401KSOURCE": INV401KSOURCES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVPOS")
        root.append(SecidTestCase.etree)
        SubElement(root, "HELDINACCT").text = "MARGIN"
        SubElement(root, "POSTYPE").text = "LONG"
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "UNITPRICE").text = "90"
        SubElement(root, "MKTVAL").text = "9000"
        SubElement(root, "AVGCOSTBASIS").text = "85"
        SubElement(root, "DTPRICEASOF").text = "20130630000000.000[0:GMT]"
        root.append(CurrencyTestCase.etree)
        SubElement(root, "MEMO").text = "Marked to myth"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVPOS(secid=SecidTestCase.aggregate,
                      heldinacct="MARGIN", postype="LONG",
                      units=Decimal("100"), unitprice=Decimal("90"),
                      mktval=Decimal("9000"), avgcostbasis=Decimal("85"),
                      dtpriceasof=datetime(2013, 6, 30, tzinfo=UTC),
                      currency=CurrencyTestCase.aggregate,
                      memo="Marked to myth", inv401ksource="PROFITSHARING")


class PosdebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSDEBT")
        invpos = InvposTestCase.etree
        root.append(invpos)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSDEBT(invpos=InvposTestCase.aggregate)

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosmfTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["UNITSSTREET", "UNITSUSER", "REINVDIV", "REINVCG"]
    oneOf = {"REINVDIV": ("Y", "N")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSMF")
        invpos = InvposTestCase.etree
        root.append(invpos)
        SubElement(root, "UNITSSTREET").text = "200"
        SubElement(root, "UNITSUSER").text = "300"
        SubElement(root, "REINVDIV").text = "N"
        SubElement(root, "REINVCG").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSMF(invpos=InvposTestCase.aggregate,
                     unitsstreet=Decimal("200"), unitsuser=Decimal("300"),
                     reinvdiv=False, reinvcg=True)

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["SECURED"]
    oneOfs = {"SECURED": ("NAKED", "COVERED")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSOPT")
        invpos = InvposTestCase.etree
        root.append(invpos)
        SubElement(root, "SECURED").text = "COVERED"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSOPT(invpos=InvposTestCase.aggregate, secured="COVERED")

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosotherTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVPOS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSOTHER")
        invpos = InvposTestCase.etree
        root.append(invpos)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSOTHER(invpos=InvposTestCase.aggregate)

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["UNITSSTREET", "UNITSUSER", "REINVDIV"]
    oneOfs = {"REINVDIV": ("Y", "N")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSSTOCK")
        invpos = InvposTestCase.etree
        root.append(invpos)
        SubElement(root, "UNITSSTREET").text = "200"
        SubElement(root, "UNITSUSER").text = "300"
        SubElement(root, "REINVDIV").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSSTOCK(invpos=InvposTestCase.aggregate,
                        unitsstreet=Decimal("200"), unitsuser=Decimal("300"),
                        reinvdiv=False)

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class InvstmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVACCTFROM", "INCOO", "INCPOS", "INCBAL"]
    optionalElements = ["INCTRAN", "INC401K", "INC401KBAL", "INCTRANIMG"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTRQ")
        root.append(InvacctfromTestCase.etree)
        root.append(InctranTestCase.etree)
        SubElement(root, "INCOO").text = "N"
        root.append(IncposTestCase.etree)
        SubElement(root, "INCBAL").text = "N"
        SubElement(root, "INC401K").text = "Y"
        SubElement(root, "INC401KBAL").text = "N"
        SubElement(root, "INCTRANIMG").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTRQ(invacctfrom=InvacctfromTestCase.aggregate,
                         inctran=InctranTestCase.aggregate, incoo=False,
                         incpos=IncposTestCase.aggregate, incbal=False,
                         inc401k=True, inc401kbal=False, inctranimg=True)


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
        #  'MKTGINFO',
        #  'INV401KBAL',
    ]
    unsupported = ("inv401k",)

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTRS")
        SubElement(root, "DTASOF").text = "20010530000000.000[0:GMT]"
        SubElement(root, "CURDEF").text = "USD"
        root.append(InvacctfromTestCase.etree)
        root.append(InvtranlistTestCase.etree)
        root.append(InvposlistTestCase.etree)
        root.append(InvbalTestCase.etree)
        # FIXME - INVOOLIST
        #  root.append(InvoolistTestCase.etree)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        # FIXME - INV401K
        #  root.append(Inv401kbalTestCase.etree)

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTRS(dtasof=datetime(2001, 5, 30, tzinfo=UTC),
                         curdef="USD",
                         invacctfrom=InvacctfromTestCase.aggregate,
                         invtranlist=InvtranlistTestCase.aggregate,
                         invposlist=InvposlistTestCase.aggregate,
                         invbal=InvbalTestCase.aggregate,
                         #  invoolist=InvoolistTestCase.aggregate,
                         mktginfo="Get Free Stuff NOW!!")
                         #  inv401kbal=Inv401kbalTestCase.aggregate,

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertIs(instance.account, instance.invacctfrom)
        cls.assertIs(instance.balances, instance.invbal)
        cls.assertIs(instance.transactions, instance.invtranlist)
        cls.assertIs(instance.positions, instance.invposlist)


class InvstmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = InvstmtrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTTRNRQ(trnuid="DEADBEEF", cltcookie="B00B135", tan="B16B00B5",
                            invstmtrq=InvstmtrqTestCase.aggregate)


class InvstmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = InvstmtrsTestCase

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        stmt = instance.statement
        cls.assertIsInstance(stmt, INVSTMTRS)

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTTRNRS(trnuid="DEADBEEF",
                            status=base.StatusTestCase.aggregate,
                            cltcookie="B00B135",
                            invstmtrs=InvstmtrsTestCase.aggregate)


class InvtranlistTestCase(unittest.TestCase, base.TranlistTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def transactions(cls):
        # Avoid circular imports in the global scope
        import test_models_invest_transactions as test_txs
        return (test_txs.InvbanktranTestCase, test_txs.BuydebtTestCase,
                test_txs.BuymfTestCase, test_txs.BuyoptTestCase,
                test_txs.BuyotherTestCase, test_txs.BuystockTestCase,
                test_txs.ClosureoptTestCase, test_txs.IncomeTestCase,
                test_txs.InvexpenseTestCase, test_txs.JrnlfundTestCase,
                test_txs.JrnlsecTestCase, test_txs.MargininterestTestCase,
                test_txs.ReinvestTestCase, test_txs.RetofcapTestCase,
                test_txs.SelldebtTestCase, test_txs.SellmfTestCase,
                test_txs.SelloptTestCase, test_txs.SellotherTestCase,
                test_txs.SellstockTestCase, test_txs.SplitTestCase,
                test_txs.TransferTestCase)

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVTRANLIST")
        SubElement(root, "DTSTART").text = "20160101000000.000[0:GMT]"
        SubElement(root, "DTEND").text = "20161231000000.000[0:GMT]"
        for tx in cls.transactions:
            root.append(tx.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        txs = [tx.aggregate for tx in cls.transactions]
        return INVTRANLIST(*txs, dtstart=datetime(2016, 1, 1, tzinfo=UTC),
                           dtend=datetime(2016, 12, 31, tzinfo=UTC))

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # Multiple contained aggregates of different types
            for transaction in cls.transactions:
                root.append(transaction.etree)
                yield root
                root.append(transaction.etree)
                yield root


if __name__ == "__main__":
    unittest.main()
