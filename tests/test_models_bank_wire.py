# coding: utf-8
"""
Unit tests for models.bank.wire
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.models.bank.wire import (
    EXTBANKDESC,
    WIREDESTBANK,
    WIREBENEFICIARY,
    WIRERQ,
    WIRERS,
    WIRECANRQ,
    WIRECANRS,
    WIRETRNRQ,
    WIRETRNRS,
)
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt


class WirebeneficiaryTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKACCTTO"]
    optionalElements = ["MEMO"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREBENEFICIARY(
            name="Elmer Fudd",
            bankacctto=bk_stmt.BankaccttoTestCase.aggregate,
            memo="For hunting wabbits",
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("WIREBENEFICIARY")
        SubElement(root, "NAME").text = "Elmer Fudd"
        root.append(bk_stmt.BankaccttoTestCase.etree)
        SubElement(root, "MEMO").text = "For hunting wabbits"
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        yield from ()


class ExtbankdescTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKID", "ADDR1", "CITY", "STATE", "POSTALCODE"]
    optionalElements = ["ADDR2", "ADDR3", "COUNTRY", "PHONE"]
    oneOfs = {"COUNTRY": COUNTRY_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return EXTBANKDESC(
            name="Lakov Trust",
            bankid="123456789",
            addr1="123 Main St",
            addr2="Suite 200",
            addr3="Attn: Transfer Dept",
            city="Dime Box",
            state="TX",
            postalcode="77853",
            country="USA",
            phone="8675309",
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("EXTBANKDESC")
        SubElement(root, "NAME").text = "Lakov Trust"
        SubElement(root, "BANKID").text = "123456789"
        SubElement(root, "ADDR1").text = "123 Main St"
        SubElement(root, "ADDR2").text = "Suite 200"
        SubElement(root, "ADDR3").text = "Attn: Transfer Dept"
        SubElement(root, "CITY").text = "Dime Box"
        SubElement(root, "STATE").text = "TX"
        SubElement(root, "POSTALCODE").text = "77853"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "PHONE").text = "8675309"
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        yield from ()


class WiredestbankTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["EXTBANKDESC"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREDESTBANK")
        root.append(ExtbankdescTestCase.etree)

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREDESTBANK(extbankdesc=ExtbankdescTestCase.aggregate)


class WirerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "WIREBENEFICIARY", "TRNAMT"]
    optionalElements = ["WIREDESTBANK", "DTDUE", "PAYINSTRUCT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIRERQ")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(WirebeneficiaryTestCase.etree)
        root.append(WiredestbankTestCase.etree)
        SubElement(root, "TRNAMT").text = "123.45"
        SubElement(root, "DTDUE").text = "17760704000000.000[+0:UTC]"
        SubElement(root, "PAYINSTRUCT").text = "Fold until all sharp corners"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIRERQ(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            wirebeneficiary=WirebeneficiaryTestCase.aggregate,
            wiredestbank=WiredestbankTestCase.aggregate,
            trnamt=Decimal("123.45"),
            dtdue=datetime(1776, 7, 4, tzinfo=UTC),
            payinstruct="Fold until all sharp corners",
        )


class WirersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "CURDEF",
        "SRVRTID",
        "BANKACCTFROM",
        "WIREBENEFICIARY",
        "TRNAMT",
    ]
    optionalElements = ["WIREDESTBANK", "DTDUE", "PAYINSTRUCT", "FEE", "CONFMSG"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIRERS(
            curdef="USD",
            srvrtid="DEADBEEF",
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            wirebeneficiary=WirebeneficiaryTestCase.aggregate,
            wiredestbank=WiredestbankTestCase.aggregate,
            trnamt=Decimal("123.45"),
            dtdue=datetime(1776, 7, 4, tzinfo=UTC),
            payinstruct="Fold until all sharp corners",
            dtxferprj=datetime(1776, 7, 4, tzinfo=UTC),
            fee=Decimal("123.45"),
            confmsg="You're good!",
        )

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("WIRERS")
        SubElement(root, "CURDEF").text = "USD"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(WirebeneficiaryTestCase.etree)
        root.append(WiredestbankTestCase.etree)
        SubElement(root, "TRNAMT").text = "123.45"
        SubElement(root, "DTDUE").text = "17760704000000.000[+0:UTC]"
        SubElement(root, "PAYINSTRUCT").text = "Fold until all sharp corners"

        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "17760704000000.000[+0:UTC]"

        dtposted = Element("DTPOSTED")
        dtposted.text = "17760704000000.000[+0:UTC]"

        for dtChoice in dtxferprj, dtposted:
            root = cls.emptyBase
            root.append(dtChoice)
            SubElement(root, "FEE").text = "123.45"
            SubElement(root, "CONFMSG").text = "You're good!"

            yield root

        # Opional mutex
        yield cls.emptyBase

    @classproperty
    @classmethod
    def invalidSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "17760704000000.000[+0:UTC]"
        dtposted = Element("DTPOSTED")
        dtposted.text = "17760704000000.000[+0:UTC]"

        # Mutex
        root = cls.emptyBase
        root.append(dtxferprj)
        root.append(dtposted)
        yield from ()


class WirecanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIRECANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIRECANRQ(srvrtid="DEADBEEF")


class WirecanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIRECANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIRECANRS(srvrtid="DEADBEEF")


class WiretrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = WirerqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIRETRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            wirerq=WirerqTestCase.aggregate,
        )


class WiretrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = WirersTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIRETRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            wirers=WirersTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
