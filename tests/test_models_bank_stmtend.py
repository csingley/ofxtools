# coding: utf-8
"""
Unit tests for models.bank.stmtend
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.models.bank.stmtend import (
    CLOSING,
    LASTPMTINFO,
    STMTENDRQ,
    STMTENDRS,
    STMTENDTRNRQ,
    STMTENDTRNRS,
    CCCLOSING,
    CCSTMTENDRQ,
    CCSTMTENDRS,
    CCSTMTENDTRNRQ,
    CCSTMTENDTRNRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_i18n as i18n
import test_models_bank_stmt as bk_stmt


class ClosingTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["FITID", "DTCLOSE", "BALCLOSE", "DTPOSTSTART", "DTPOSTEND"]
    optionalElements = [
        "DTOPEN",
        "DTNEXT",
        "BALOPEN",
        "BALMIN",
        "DEPANDCREDIT",
        "CHKANDDEBIT",
        "TOTALFEES",
        "TOTALINT",
        "MKTGINFO",
        "CURRENCY",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CLOSING")
        SubElement(root, "FITID").text = "DEADBEEF"
        SubElement(root, "DTOPEN").text = "20161201000000.000[+0:UTC]"
        SubElement(root, "DTCLOSE").text = "20161225000000.000[+0:UTC]"
        SubElement(root, "DTNEXT").text = "20170101000000.000[+0:UTC]"
        SubElement(root, "BALOPEN").text = "11"
        SubElement(root, "BALCLOSE").text = "20"
        SubElement(root, "BALMIN").text = "6"
        SubElement(root, "DEPANDCREDIT").text = "14"
        SubElement(root, "CHKANDDEBIT").text = "-5"
        SubElement(root, "TOTALFEES").text = "0"
        SubElement(root, "TOTALINT").text = "0"
        SubElement(root, "DTPOSTSTART").text = "20161201000000.000[+0:UTC]"
        SubElement(root, "DTPOSTEND").text = "20161225000000.000[+0:UTC]"
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        root.append(i18n.CurrencyTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CLOSING(
            fitid="DEADBEEF",
            dtopen=datetime(2016, 12, 1, tzinfo=UTC),
            dtclose=datetime(2016, 12, 25, tzinfo=UTC),
            dtnext=datetime(2017, 1, 1, tzinfo=UTC),
            balopen=Decimal("11"),
            balclose=Decimal("20"),
            balmin=Decimal("6"),
            depandcredit=Decimal("14"),
            chkanddebit=Decimal("-5"),
            totalfees=Decimal("0"),
            totalint=Decimal("0"),
            dtpoststart=datetime(2016, 12, 1, tzinfo=UTC),
            dtpostend=datetime(2016, 12, 25, tzinfo=UTC),
            mktginfo="Get Free Stuff NOW!!",
            currency=i18n.CurrencyTestCase.aggregate,
        )


class StmtendrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM"]
    optionalElements = ["DTSTART", "DTEND"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STMTENDRQ")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        SubElement(root, "DTSTART").text = "20161201000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20161225000000.000[+0:UTC]"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTENDRQ(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            dtstart=datetime(2016, 12, 1, tzinfo=UTC),
            dtend=datetime(2016, 12, 25, tzinfo=UTC),
        )


class StmtendrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM"]
    optionalElements = ["CLOSING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STMTENDRS")
        SubElement(root, "CURDEF").text = "CAD"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        closing = ClosingTestCase.etree
        root.append(closing)
        root.append(closing)

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTENDRS(
            ClosingTestCase.aggregate,
            ClosingTestCase.aggregate,
            curdef="CAD",
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )


class StmtendtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StmtendrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTENDTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            stmtendrq=StmtendrqTestCase.aggregate,
        )


class StmtendtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StmtendrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTENDTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            stmtendrs=StmtendrsTestCase.aggregate,
        )


class LastpmtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("LASTPMTINFO")
        SubElement(root, "LASTPMTDATE").text = "20170501000000.000[+0:UTC]"
        SubElement(root, "LASTPMTAMT").text = "655.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return LASTPMTINFO(
            lastpmtdate=datetime(2017, 5, 1, tzinfo=UTC), lastpmtamt=Decimal("655.50")
        )


class CcclosingTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["FITID", "DTCLOSE", "BALCLOSE", "DTPOSTSTART", "DTPOSTEND"]
    optionalElements = [
        "DTOPEN",
        "DTNEXT",
        "BALOPEN",
        "INTYTD",
        "DTPMTDUE",
        "MINPMTDUE",
        "PASTDUEAMT",
        "LATEFEEAMT",
        "FINCHG",
        "INTRATEPURCH",
        "INTRATECASH",
        "INTRATEXFER",
        "PAYANDCREDIT",
        "PURANDADV",
        "DEBADJ",
        "CREDITLIMIT",
        "CASHADVCREDITLIMIT",
        "AUTOPAY",
        "LASTPMTINFO",
        "REWARDINFO",
        "MKTGINFO",
        "CURRENCY",
    ]
    unsupported = ["imagedata"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCCLOSING")
        SubElement(root, "FITID").text = "1001"
        SubElement(root, "DTOPEN").text = "20040701000000.000[+0:UTC]"
        SubElement(root, "DTCLOSE").text = "20040704000000.000[+0:UTC]"
        SubElement(root, "DTNEXT").text = "20040804000000.000[+0:UTC]"
        SubElement(root, "BALOPEN").text = "24.5"
        SubElement(root, "BALCLOSE").text = "26.5"
        SubElement(root, "INTYTD").text = "0.01"
        SubElement(root, "DTPMTDUE").text = "20040715000000.000[+0:UTC]"
        SubElement(root, "MINPMTDUE").text = "7.65"
        SubElement(root, "PASTDUEAMT").text = "0.35"
        SubElement(root, "LATEFEEAMT").text = "5"
        SubElement(root, "FINCHG").text = "0.5"
        SubElement(root, "INTRATEPURCH").text = "26"
        SubElement(root, "INTRATECASH").text = "30"
        SubElement(root, "INTRATEXFER").text = "28"
        SubElement(root, "PAYANDCREDIT").text = "1.5"
        SubElement(root, "PURANDADV").text = "2.75"
        SubElement(root, "DEBADJ").text = "1.45"
        SubElement(root, "CREDITLIMIT").text = "50000"
        SubElement(root, "CASHADVCREDITLIMIT").text = "5000"
        SubElement(root, "DTPOSTSTART").text = "20040701000000.000[+0:UTC]"
        SubElement(root, "DTPOSTEND").text = "20040704000000.000[+0:UTC]"
        SubElement(root, "AUTOPAY").text = "Y"
        lastpmtinfo = LastpmtinfoTestCase.etree
        root.append(lastpmtinfo)
        rewardinfo = bk_stmt.RewardinfoTestCase.etree
        root.append(rewardinfo)
        SubElement(root, "MKTGINFO").text = "It's a floor wax! And a dessert topping!!"
        currency = i18n.CurrencyTestCase.etree
        root.append(currency)

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCCLOSING(
            fitid="1001",
            dtopen=datetime(2004, 7, 1, tzinfo=UTC),
            dtclose=datetime(2004, 7, 4, tzinfo=UTC),
            dtnext=datetime(2004, 8, 4, tzinfo=UTC),
            balopen=Decimal("24.5"),
            balclose=Decimal("26.5"),
            intytd=Decimal("0.01"),
            dtpmtdue=datetime(2004, 7, 15, tzinfo=UTC),
            minpmtdue=Decimal("7.65"),
            pastdueamt=Decimal("0.35"),
            latefeeamt=Decimal("5"),
            finchg=Decimal("0.5"),
            intratepurch=Decimal("26"),
            intratecash=Decimal("30"),
            intratexfer=Decimal("28"),
            payandcredit=Decimal("1.5"),
            purandadv=Decimal("2.75"),
            debadj=Decimal("1.45"),
            creditlimit=Decimal("50000"),
            cashadvcreditlimit=Decimal("5000"),
            dtpoststart=datetime(2004, 7, 1, tzinfo=UTC),
            dtpostend=datetime(2004, 7, 4, tzinfo=UTC),
            autopay=True,
            lastpmtinfo=LastpmtinfoTestCase.aggregate,
            rewardinfo=bk_stmt.RewardinfoTestCase.aggregate,
            mktginfo="It's a floor wax! And a dessert topping!!",
            currency=i18n.CurrencyTestCase.aggregate,
        )


class CcstmtendrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CCACCTFROM"]
    optionalElements = ["DTSTART", "DTEND", "INCSTMTIMG"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCSTMTENDRQ")
        acctfrom = bk_stmt.CcacctfromTestCase.etree
        root.append(acctfrom)
        SubElement(root, "DTSTART").text = "20040701000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20040704000000.000[+0:UTC]"
        SubElement(root, "INCSTMTIMG").text = "N"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTENDRQ(
            ccacctfrom=bk_stmt.CcacctfromTestCase.aggregate,
            dtstart=datetime(2004, 7, 1, tzinfo=UTC),
            dtend=datetime(2004, 7, 4, tzinfo=UTC),
            incstmtimg=False,
        )


class CcstmtendrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "CCACCTFROM"]
    optionalElements = ["CCCLOSING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCSTMTENDRS")
        SubElement(root, "CURDEF").text = "USD"
        acctfrom = bk_stmt.CcacctfromTestCase.etree
        root.append(acctfrom)
        ccclosing = CcclosingTestCase.etree
        root.append(ccclosing)
        root.append(ccclosing)

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTENDRS(
            CcclosingTestCase.aggregate,
            CcclosingTestCase.aggregate,
            curdef="USD",
            ccacctfrom=bk_stmt.CcacctfromTestCase.aggregate,
        )


class CcstmtendtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = CcstmtendrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTENDTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            ccstmtendrq=CcstmtendrqTestCase.aggregate,
        )


class CcstmtendtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = CcstmtendrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTENDTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            ccstmtendrs=CcstmtendrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
