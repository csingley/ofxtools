# coding: utf-8
"""
Unit tests for models.bank.xfer
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.bank.xfer import (
    XFERINFO,
    XFERPRCSTS,
    INTRARQ,
    INTRARS,
    INTRAMODRQ,
    INTRACANRQ,
    INTRAMODRS,
    INTRACANRS,
    INTRATRNRQ,
    INTRATRNRS,
)
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt


class XferinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNAMT"]
    optionalElements = ["DTDUE"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return XFERINFO(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            bankacctto=bk_stmt.BankaccttoTestCase.aggregate,
            trnamt=Decimal("257.53"),
            dtdue=datetime(2008, 9, 30, tzinfo=UTC),
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        bankacctto = bk_stmt.BankaccttoTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        ccacctto = bk_stmt.CcaccttoTestCase.etree

        for acctfrom in (bankacctfrom, ccacctfrom):
            for acctto in (bankacctto, ccacctto):
                root = Element("XFERINFO")
                root.append(acctfrom)
                root.append(acctto)
                SubElement(root, "TRNAMT").text = "257.53"
                SubElement(root, "DTDUE").text = "20080930000000.000[+0:UTC]"
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        root_ = Element("XFERINFO")

        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        bankacctto = bk_stmt.BankaccttoTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        ccacctto = bk_stmt.CcaccttoTestCase.etree
        trnamt = Element("TRNAMT")
        trnamt.text = "257.53"

        # requiredMutexes = [("bankacctfrom", "ccacctfrom"), ("bankacctto", "ccacctto")]
        # Missing BANKACCTFROM/CCACCTFROM
        root = deepcopy(root_)
        root.append(bankacctto)
        root.append(trnamt)
        yield root

        root = deepcopy(root_)
        root.append(bankacctfrom)
        root.append(trnamt)
        yield root

        # Both BANKACCTFROM & CCACCTFROM / BANKACCTTO & CCACCTTO
        root = deepcopy(root_)
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(trnamt)
        yield root

        root = deepcopy(root_)
        root.append(bankacctto)
        root.append(ccacctto)
        root.append(trnamt)
        yield root

        #  FIXME - Check out-of-order errors


class XferprcstsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERPRCCODE", "DTXFERPRC"]
    oneOfs = {
        "XFERPRCCODE": [
            "WILLPROCESSON",
            "POSTEDON",
            "NOFUNDSON",
            "CANCELEDON",
            "FAILEDON",
        ]
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("XFERPRCSTS")
        SubElement(root, "XFERPRCCODE").text = "POSTEDON"
        SubElement(root, "DTXFERPRC").text = "20071231000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return XFERPRCSTS(
            xferprccode="POSTEDON", dtxferprc=datetime(2007, 12, 31, tzinfo=UTC)
        )


class IntrarqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTRARQ")
        root.append(XferinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRARQ(xferinfo=XferinfoTestCase.aggregate)


class IntrarsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "XFERINFO"]
    optionalElements = ["RECSRVRTID", "XFERPRCSTS"]
    oneOfs = {"CURDEF": CURRENCY_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTRARS")
        SubElement(root, "CURDEF").text = "EUR"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(XferinfoTestCase.etree)
        SubElement(root, "RECSRVRTID").text = "B16B00B5"
        root.append(XferprcstsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRARS(
            curdef="EUR",
            srvrtid="DEADBEEF",
            xferinfo=XferinfoTestCase.aggregate,
            recsrvrtid="B16B00B5",
            xferprcsts=XferprcstsTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        for dtChoice in (None, dtxferprj, dtposted):
            root = Element("INTRARS")
            SubElement(root, "CURDEF").text = "EUR"
            SubElement(root, "SRVRTID").text = "DEADBEEF"
            xferinfo = XferinfoTestCase.etree
            root.append(xferinfo)
            if dtChoice is not None:
                root.append(dtChoice)
            SubElement(root, "RECSRVRTID").text = "B16B00B5"
            xferprcsts = XferprcstsTestCase.etree
            root.append(xferprcsts)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [("dtxferprj", "dtposted")]
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        root = Element("INTRARS")
        SubElement(root, "CURDEF").text = "EUR"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase.etree
        root.append(xferinfo)
        root.append(dtxferprj)
        root.append(dtposted)

        yield root


class IntramodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTRAMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(XferinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRAMODRQ(srvrtid="DEADBEEF", xferinfo=XferinfoTestCase.aggregate)


class IntracanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTRACANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRACANRQ(srvrtid="DEADBEEF")


class IntramodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTRAMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(XferinfoTestCase.etree)
        root.append(XferprcstsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRAMODRS(
            srvrtid="DEADBEEF",
            xferinfo=XferinfoTestCase.aggregate,
            xferprcsts=XferprcstsTestCase.aggregate,
        )


class IntracanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTRACANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRACANRS(srvrtid="DEADBEEF")


class IntratrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = IntrarqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRATRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            intrarq=IntrarqTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in IntrarqTestCase, IntramodrqTestCase, IntracanrqTestCase:
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

        #  requiredMutex= ("intrarq", "intramodrq", "intracanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTRARQ/INTRAMODRQ/INTRACANRQ
        yield root

        # Multiple INTRARQ/INTRAMODRQ/INTRACANRQ
        for Tests in [
            (IntrarqTestCase, IntramodrqTestCase),
            (IntrarqTestCase, IntracanrqTestCase),
            (IntramodrqTestCase, IntracanrqTestCase),
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


class IntratrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = IntrarsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTRATRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            intrars=IntrarsTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in IntrarsTestCase, IntramodrsTestCase, IntracanrsTestCase:
            root = cls.emptyBase
            rs = Test.etree
            root.append(rs)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        root_ = Element(tag)

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
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("intrars", "intramodrs", "intracanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTRARS/INTRAMODRS/INTRACANRS
        yield root

        # Multiple INTRARS/INTRAMODRS/INTRACANRS
        for Tests in [
            (IntrarsTestCase, IntramodrsTestCase),
            (IntrarsTestCase, IntracanrsTestCase),
            (IntramodrsTestCase, IntracanrsTestCase),
        ]:
            root = deepcopy(cls.emptyBase)
            for Test in Tests:
                root.append(Test.etree)
            yield root

        # Wrapped aggregate in the wrong place (should be right after CLTCOOKIE)
        index = list(root_).index(root_.find("CLTCOOKIE"))
        for n in range(index):
            root = cls.emptyBase
            root.insert(n, cls.wrapped)
            yield root


if __name__ == "__main__":
    unittest.main()
