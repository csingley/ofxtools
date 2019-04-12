# coding: utf-8
"""
Unit tests for models.bank.stpchk
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.bank.stpchk import CHKRANGE, CHKDESC, STPCHKNUM, STPCHKRS
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_i18n import CurrencyTestCase, OrigcurrencyTestCase
from test_models_bank_stmt import BankacctfromTestCase


class ChkrangeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CHKNUMSTART"]
    optionalElements = ["CHKNUMEND"]

    @property
    def root(self):
        root = Element("CHKRANGE")
        SubElement(root, "CHKNUMSTART").text = "123"
        SubElement(root, "CHKNUMEND").text = "125"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHKRANGE)
        self.assertEqual(instance.chknumstart, "123")
        self.assertEqual(instance.chknumend, "125")


class ChkdescTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME"]
    optionalElements = ["CHKNUM", "DTUSER", "TRNAMT"]

    @property
    def root(self):
        root = Element("CHKDESC")
        SubElement(root, "NAME").text = "Bucky Beaver"
        SubElement(root, "CHKNUM").text = "125"
        SubElement(root, "DTUSER").text = "20051122"
        SubElement(root, "TRNAMT").text = "2533"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHKDESC)
        self.assertEqual(instance.name, "Bucky Beaver")
        self.assertEqual(instance.dtuser, datetime(2005, 11, 22, tzinfo=UTC))
        self.assertEqual(instance.trnamt, Decimal("2533"))


class StpchkrqTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKRQ with CHKRANGE """

    __test__ = True

    requiredElements = ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STPCHKRQ")
        root.append(BankacctfromTestCase().root)
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        chkrange = ChkrangeTestCase().root
        chkdesc = ChkdescTestCase().root
        for choice in chkrange, chkdesc:
            root = cls.emptyBase
            root.append(choice)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        chkrange = ChkrangeTestCase().root
        chkdesc = ChkdescTestCase().root

        #  requiredMutexes = [("chkrange", "chkdesc")]
        #  Neither
        root = cls.emptyBase
        yield root
        #  Both
        root.append(chkrange)
        root.append(chkdesc)
        yield root

        #  FIXME
        #  Check out-of-order errors


class StpchknumTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKNUM with CURRENCY """

    __test__ = True

    requiredElements = ["CHECKNUM", "CHKSTATUS"]
    optionalElements = ["NAME", "DTUSER", "TRNAMT", "CHKERROR"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STPCHKNUM")
        SubElement(root, "CHECKNUM").text = "123"
        SubElement(root, "NAME").text = "Buckaroo Banzai"
        SubElement(root, "DTUSER").text = "17760704"
        SubElement(root, "TRNAMT").text = "4500"
        SubElement(root, "CHKSTATUS").text = "0"
        SubElement(root, "CHKERROR").text = "Stop check succeeded"

        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        currency = CurrencyTestCase().root
        origcurrency = OrigcurrencyTestCase().root
        for currencyChoice in (None, currency, origcurrency):
            root = deepcopy(cls.emptyBase)
            if currencyChoice is not None:
                root.append(currencyChoice)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [("currency", "origcurrency")]
        currency = CurrencyTestCase().root
        origcurrency = OrigcurrencyTestCase().root

        root = deepcopy(cls.emptyBase)
        root.append(currency)
        root.append(origcurrency)
        yield root

    def testOneOf(self):
        self.oneOfTest("CHKSTATUS", ["0", "1", "100", "101"])


class StpchkrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM", "FEE", "FEEMSG"]

    @property
    def root(self):
        root = Element("STPCHKRS")
        SubElement(root, "CURDEF").text = "CAD"
        root.append(BankacctfromTestCase().root)
        #  SubElement(root, "FEE").text = "25"
        #  SubElement(root, "FEEMSG").text = "Shit's expensive yo"
        stpchknum = StpchknumTestCase().root
        root.append(stpchknum)
        root.append(deepcopy(stpchknum))
        SubElement(root, "FEE").text = "25"
        SubElement(root, "FEEMSG").text = "Shit's expensive yo"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKRS)
        self.assertEqual(instance.curdef, "CAD")
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], STPCHKNUM)
        self.assertIsInstance(instance[1], STPCHKNUM)
        self.assertEqual(instance.fee, Decimal("25"))
        self.assertEqual(instance.feemsg, "Shit's expensive yo")


class StpchktrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StpchkrqTestCase


class StpchktrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StpchkrsTestCase


if __name__ == "__main__":
    unittest.main()
