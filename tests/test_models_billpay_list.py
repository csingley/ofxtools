# coding: utf-8
""" Unit tests for models.billpay.common """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.billpay.list import (
    PAYEERQ,
    PAYEERS,
    PAYEEMODRQ,
    PAYEEMODRS,
    PAYEEDELRQ,
    PAYEEDELRS,
    PAYEETRNRQ,
    PAYEETRNRS,
)
from ofxtools.utils import classproperty


# test imports
import base
import test_models_bank_stmt as bank_stmt
import test_models_billpay_common as bp_common


class PayeerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        #  return next(cls.validSoup)
        return list(cls.validSoup)[-1]

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEERQ(
            "123",
            "123",
            payee=bank_stmt.PayeeTestCase.aggregate,
            bankacctto=bank_stmt.BankaccttoTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        payeeid = Element("PAYEEID")
        payeeid.text = "DEADBEEF"
        payee = bank_stmt.PayeeTestCase.etree
        bankacctto = bank_stmt.BankaccttoTestCase.etree
        payacct = Element("PAYACCT")
        payacct.text = "123"

        for choice in payeeid, payee:
            root = Element("PAYEERQ")
            root.append(choice)
            root.append(bankacctto)
            yield root
            for i in range(2):
                root.append(payacct)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        payeeid = Element("PAYEE")
        payeeid.text = "DEADBEEF"
        payee = bank_stmt.PayeeTestCase.etree
        bankacctto = bank_stmt.BankaccttoTestCase.etree
        payacct = Element("PAYACCT")
        payacct.text = "123"

        # Neither PAYEE nor PAYEEID
        root = Element("PAYEERQ")
        root.append(bankacctto)
        root.append(payacct)
        yield root

        # Both PAYEEID and PAYEE
        root = Element("PAYEERQ")
        root.append(payeeid)
        root.append(payee)
        root.append(bankacctto)
        root.append(payacct)
        yield root


class PayeersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]
    optionalElements = ["PAYEE", "BANKACCTTO", "EXTDPAYEE", "PAYACCT"]

    @classproperty
    @classmethod
    def etree(cls):
        return list(cls.validSoup)[-1]

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEERS(
            "12345",
            "12345",
            payeelstid="B16B00B5",
            payee=bank_stmt.PayeeTestCase.aggregate,
            bankacctto=bank_stmt.BankaccttoTestCase.aggregate,
            extdpayee=bp_common.ExtdpayeeTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("PAYEERS")
        SubElement(root, "PAYEELSTID").text = "B16B00B5"
        root.append(bank_stmt.PayeeTestCase.etree)
        root.append(bank_stmt.BankaccttoTestCase.etree)
        root.append(bp_common.ExtdpayeeTestCase.etree)
        yield root
        for i in range(2):
            SubElement(root, "PAYACCT").text = "12345"
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # FIXME
        yield from ()


class PayeemodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]
    optionalElements = ["PAYEE", "BANKACCTTO", "PAYACCT"]

    @classproperty
    @classmethod
    def etree(cls):
        return list(cls.validSoup)[-1]

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEEMODRQ(
            "12345",
            "12345",
            payeelstid="DEADBEEF",
            payee=bank_stmt.PayeeTestCase.aggregate,
            bankacctto=bank_stmt.BankaccttoTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("PAYEEMODRQ")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        root.append(bank_stmt.PayeeTestCase.etree)
        root.append(bank_stmt.BankaccttoTestCase.etree)
        yield root
        for i in range(2):
            SubElement(root, "PAYACCT").text = "12345"
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # FIXME
        yield from ()


class PayeemodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]
    optionalElements = ["PAYEE", "BANKACCTTO", "PAYACCT", "EXTDPAYEE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PAYEEMODRS")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        root.append(bank_stmt.PayeeTestCase.etree)
        root.append(bank_stmt.BankaccttoTestCase.etree)
        SubElement(root, "PAYACCT").text = "12345"
        SubElement(root, "PAYACCT").text = "12345"
        root.append(bp_common.ExtdpayeeTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEEMODRS(
            "12345",
            "12345",
            payeelstid="DEADBEEF",
            payee=bank_stmt.PayeeTestCase.aggregate,
            bankacctto=bank_stmt.BankaccttoTestCase.aggregate,
            extdpayee=bp_common.ExtdpayeeTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for i in range(3):
            root = Element("PAYEEMODRS")
            SubElement(root, "PAYEELSTID").text = "DEADBEEF"
            root.append(bank_stmt.PayeeTestCase.etree)
            root.append(bank_stmt.BankaccttoTestCase.etree)
            for n in range(i):
                SubElement(root, "PAYACCT").text = "12345"
            root.append(bp_common.ExtdpayeeTestCase.etree)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # FIXME
        yield from ()


class PayeedelrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PAYEEDELRQ")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEEDELRQ(payeelstid="DEADBEEF")


class PayeedelrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PAYEEDELRS")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEEDELRS(payeelstid="DEADBEEF")


class PayeetrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PayeerqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEETRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            payeerq=PayeerqTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in PayeerqTestCase, PayeemodrqTestCase, PayeedelrqTestCase:
            root = cls.emptyBase
            rq = Test.etree
            root.append(rq)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        root_ = Element(tag)

        # TRNUID/COOKIE/TAN out of order
        trnuid = Element("TRNUID")
        trnuid.text = "DEADBEEF"
        cltcookie = Element("CLTCOOKIE")
        cltcookie.text = "B00B135"
        tan = Element("TAN")
        tan.text = "B16B00B5"

        legal = [trnuid, cltcookie, tan]
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
                continue
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("payeerq", "payeemodrq", "payeedelrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing PAYEERQ/PAYEEMODRQ/PAYEEDELRQ
        yield root

        # Multiple PAYEERQ/PAYEEMODRQ/PAYEEDELRQ
        for Tests in [
            (PayeerqTestCase, PayeemodrqTestCase),
            (PayeerqTestCase, PayeedelrqTestCase),
            (PayeemodrqTestCase, PayeedelrqTestCase),
        ]:
            root = deepcopy(cls.emptyBase)
            for Test in Tests:
                root.append(Test.etree)
            yield root

        # Wrapped aggregate in the wrong place (should be right after TAN)

        root_ = deepcopy(cls.emptyBase)
        index = list(root_).index(root_.find("TAN"))
        for n in range(index):
            root = deepcopy(root_)
            root.insert(n, cls.wrapped)
            yield root


class PayeetrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PayeersTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEETRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            payeers=PayeersTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in PayeersTestCase, PayeemodrsTestCase, PayeedelrsTestCase:
            root = deepcopy(cls.emptyBase)
            rs = Test.etree
            root.append(rs)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()

        # TRNUID/STATUS/CLTCOOKIE out of order
        trnuid = Element("TRNUID")
        trnuid.text = "DEADBEEF"
        status = base.StatusTestCase.etree
        cltcookie = Element("CLTCOOKIE")
        cltcookie.text = "B00B135"

        legal = [trnuid, status, cltcookie]
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
                continue
            root = Element(tag)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex = ("payeers", "payeemodrs", "payeemodrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing PAYEERS/PAYEEMODRS/PAYEEMODRS
        yield root

        # Multiple PAYEERS/PAYEEMODRS/PAYEEMODRS
        for Tests in [
            (PayeersTestCase, PayeemodrsTestCase),
            (PayeersTestCase, PayeemodrsTestCase),
            (PayeemodrsTestCase, PayeedelrsTestCase),
        ]:
            root = deepcopy(cls.emptyBase)
            for Test in Tests:
                root.append(Test.etree)
            yield root

        # Wrapped aggregate in the wrong place (should be right after CLTCOOKIE)
        root_ = deepcopy(cls.emptyBase)
        index = list(root_).index(root_.find("CLTCOOKIE"))
        for n in range(index):
            root = deepcopy(root_)
            root.insert(n, cls.wrapped)
            yield root


if __name__ == "__main__":
    unittest.main()
