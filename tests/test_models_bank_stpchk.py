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
from ofxtools.models.bank.stpchk import (
    CHKRANGE,
    CHKDESC,
    STPCHKNUM,
    STPCHKRQ,
    STPCHKRS,
    STPCHKTRNRQ,
    STPCHKTRNRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_i18n as i18n
import test_models_bank_stmt as bk_stmt


class ChkrangeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CHKNUMSTART"]
    optionalElements = ["CHKNUMEND"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CHKRANGE")
        SubElement(root, "CHKNUMSTART").text = "123"
        SubElement(root, "CHKNUMEND").text = "125"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHKRANGE(chknumstart="123", chknumend="125")


class ChkdescTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME"]
    optionalElements = ["CHKNUM", "DTUSER", "TRNAMT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CHKDESC")
        SubElement(root, "NAME").text = "Bucky Beaver"
        SubElement(root, "CHKNUM").text = "125"
        SubElement(root, "DTUSER").text = "20051122000000.000[+0:UTC]"
        SubElement(root, "TRNAMT").text = "2533"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHKDESC(
            name="Bucky Beaver",
            chknum="125",
            dtuser=datetime(2005, 11, 22, tzinfo=UTC),
            trnamt=Decimal("2533"),
        )


class StpchkrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKRQ(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            chkrange=ChkrangeTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STPCHKRQ")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        chkrange = ChkrangeTestCase.etree
        chkdesc = ChkdescTestCase.etree
        for choice in chkrange, chkdesc:
            root = cls.emptyBase
            root.append(choice)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        chkrange = ChkrangeTestCase.etree
        chkdesc = ChkdescTestCase.etree

        #  requiredMutexes = [("chkrange", "chkdesc")]
        #  Neither
        root = cls.emptyBase
        yield root
        #  Both
        root.append(chkrange)
        root.append(chkdesc)
        yield root

        #  FIXME - test out-of-order errors


class StpchknumTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CHECKNUM", "CHKSTATUS"]
    optionalElements = ["NAME", "DTUSER", "TRNAMT", "CHKERROR"]
    oneOfs = {"CHKSTATUS": ["0", "1", "100", "101"]}

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKNUM(
            checknum="123",
            name="Buckaroo Banzai",
            dtuser=datetime(1776, 7, 4, tzinfo=UTC),
            trnamt=Decimal("4500.00"),
            chkstatus="0",
            chkerror="Stop check succeeded",
        )

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STPCHKNUM")
        SubElement(root, "CHECKNUM").text = "123"
        SubElement(root, "NAME").text = "Buckaroo Banzai"
        SubElement(root, "DTUSER").text = "17760704000000.000[+0:UTC]"
        SubElement(root, "TRNAMT").text = "4500.00"
        SubElement(root, "CHKSTATUS").text = "0"
        SubElement(root, "CHKERROR").text = "Stop check succeeded"
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        currency = i18n.CurrencyTestCase.etree
        origcurrency = i18n.OrigcurrencyTestCase.etree
        for currencyChoice in (None, currency, origcurrency):
            root = deepcopy(cls.emptyBase)
            if currencyChoice is not None:
                root.append(currencyChoice)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [("currency", "origcurrency")]
        currency = i18n.CurrencyTestCase.etree
        origcurrency = i18n.OrigcurrencyTestCase.etree

        root = deepcopy(cls.emptyBase)
        root.append(currency)
        root.append(origcurrency)
        yield root


class StpchkrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM", "FEE", "FEEMSG"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STPCHKRS")
        SubElement(root, "CURDEF").text = "CAD"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        stpchknum = StpchknumTestCase.etree
        root.append(stpchknum)
        root.append(stpchknum)
        SubElement(root, "FEE").text = "25"
        SubElement(root, "FEEMSG").text = "Shit's expensive yo"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKRS(
            StpchknumTestCase.aggregate,
            StpchknumTestCase.aggregate,
            curdef="CAD",
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            fee=Decimal("25"),
            feemsg="Shit's expensive yo",
        )


class StpchktrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StpchkrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            stpchkrq=StpchkrqTestCase.aggregate,
        )


class StpchktrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StpchkrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            stpchkrs=StpchkrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
