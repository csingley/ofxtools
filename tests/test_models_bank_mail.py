# coding: utf-8
"""
Unit tests for models.bank.mail
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.models.bank.mail import (
    BANKMAILRQ,
    BANKMAILRS,
    BANKMAILTRNRQ,
    BANKMAILTRNRS,
    CHKMAILRS,
    DEPMAILRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_email as email
import test_models_bank_stmt as bk_stmt


class BankmailrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMAILRQ(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            mail=email.MailTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        mail = email.MailTestCase.etree
        for acctfrom in bankacctfrom, ccacctfrom:
            root = Element("BANKMAILRQ")
            root.append(acctfrom)
            root.append(mail)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        mail = email.MailTestCase.etree

        #  requiredMutexes = [("bankacctfrom", "ccacctfrom")]
        #  Neither
        root = Element("BANKMAILRQ")
        root.append(mail)
        yield root
        #  Both
        root = Element("BANKMAILRQ")
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(mail)
        yield root

        #  FIXME - Check out-of-order errors


class BankmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMAILRS(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            mail=email.MailTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        mail = email.MailTestCase.etree
        for acctfrom in bankacctfrom, ccacctfrom:
            root = Element("BANKMAILRS")
            root.append(acctfrom)
            root.append(mail)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        mail = email.MailTestCase.etree

        #  requiredMutexes = [("bankacctfrom", "ccacctfrom")]
        #  Neither
        root = Element("BANKMAILRS")
        root.append(mail)
        yield root
        #  Both
        root = Element("BANKMAILRS")
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(mail)
        yield root

        #  FIXME - Check out-of-order errors


class ChkmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "MAIL", "CHECKNUM"]
    optionalElements = ["TRNAMT", "DTUSER", "FEE"]

    @classproperty
    @classmethod
    def etree(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        mail = email.MailTestCase.etree

        root = Element("CHKMAILRS")
        root.append(bankacctfrom)
        root.append(mail)
        SubElement(root, "CHECKNUM").text = "1001"
        SubElement(root, "TRNAMT").text = "321.45"
        SubElement(root, "DTUSER").text = "21060930000000.000[+0:UTC]"
        SubElement(root, "FEE").text = "21.50"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHKMAILRS(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            mail=email.MailTestCase.aggregate,
            checknum="1001",
            trnamt=Decimal("321.45"),
            dtuser=datetime(2106, 9, 30, tzinfo=UTC),
            fee=Decimal("21.50"),
        )


class DepmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "MAIL", "TRNAMT"]
    optionalElements = ["DTUSER", "FEE"]

    @classproperty
    @classmethod
    def etree(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        mail = email.MailTestCase.etree

        root = Element("DEPMAILRS")
        root.append(bankacctfrom)
        root.append(mail)
        SubElement(root, "TRNAMT").text = "321.45"
        SubElement(root, "DTUSER").text = "21060930000000.000[+0:UTC]"
        SubElement(root, "FEE").text = "21.50"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return DEPMAILRS(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            mail=email.MailTestCase.aggregate,
            trnamt=Decimal("321.45"),
            dtuser=datetime(2106, 9, 30, tzinfo=UTC),
            fee=Decimal("21.50"),
        )


class BankmailtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = BankmailrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMAILTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            bankmailrq=BankmailrqTestCase.aggregate,
        )


class BankmailtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = BankmailrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMAILTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            bankmailrs=BankmailrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
