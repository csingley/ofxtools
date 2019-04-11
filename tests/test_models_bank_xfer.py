# coding: utf-8
"""
Unit tests for models.bank.xfer
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.bank.xfer import (
    XFERINFO,
    XFERPRCSTS,
    INTRARQ,
    INTRAMODRQ,
    INTRACANRQ,
    INTRAMODRS,
    INTRACANRS,
)
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_bank_stmt import (
    BankacctfromTestCase,
    BankaccttoTestCase,
    CcacctfromTestCase,
    CcaccttoTestCase,
)


class XferinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNAMT"]
    optionalElements = ["DTDUE"]

    @classproperty
    @classmethod
    def validSoup(cls):
        bankacctfrom = BankacctfromTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        ccacctto = CcaccttoTestCase().root

        for acctfrom in (bankacctfrom, ccacctfrom):
            for acctto in (bankacctto, ccacctto):
                root = Element("XFERINFO")
                root.append(acctfrom)
                root.append(acctto)
                SubElement(root, "TRNAMT").text = "257.53"
                SubElement(root, "DTDUE").text = "20080930000000"
                yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        root_ = Element("XFERINFO")

        bankacctfrom = BankacctfromTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        ccacctto = CcaccttoTestCase().root
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

        # FIXME
        # test out-of-order errors

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class XferprcstsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERPRCCODE", "DTXFERPRC"]

    @property
    def root(self):
        root = Element("XFERPRCSTS")
        SubElement(root, "XFERPRCCODE").text = "POSTEDON"
        SubElement(root, "DTXFERPRC").text = "20071231000000"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, XFERPRCSTS)
        self.assertEqual(instance.xferprccode, "POSTEDON")
        self.assertEqual(instance.dtxferprc, datetime(2007, 12, 31, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest(
            "XFERPRCCODE",
            ["WILLPROCESSON", "POSTEDON", "NOFUNDSON", "CANCELEDON", "FAILEDON"],
        )


class IntrarqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERINFO"]

    @property
    def root(self):
        root = Element("INTRARQ")
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRARQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)


class IntrarsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "XFERINFO"]
    optionalElements = ["RECSRVRTID", "XFERPRCSTS"]

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
            xferinfo = XferinfoTestCase().root
            root.append(xferinfo)
            if dtChoice is not None:
                root.append(dtChoice)
            SubElement(root, "RECSRVRTID").text = "B16B00B5"
            xferprcsts = XferprcstsTestCase().root
            root.append(xferprcsts)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

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
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)
        root.append(dtxferprj)
        root.append(dtposted)

        yield root

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest("CURDEF", CURRENCY_CODES)


class IntramodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @property
    def root(self):
        root = Element("INTRAMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRAMODRQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntracanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("INTRACANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRACANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntramodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @property
    def root(self):
        root = Element("INTRAMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)
        xferprcsts = XferprcstsTestCase().root
        root.append(xferprcsts)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRAMODRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertIsInstance(instance.xferprcsts, XFERPRCSTS)


class IntracanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("INTRACANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRACANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntratrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = IntrarqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in IntrarqTestCase, IntramodrqTestCase, IntracanrqTestCase:
            root = deepcopy(cls.emptyBase)
            rq = Test().root
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
                root.append(Test().root)
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

    wraps = IntrarqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in IntrarsTestCase, IntramodrsTestCase, IntracanrsTestCase:
            root = deepcopy(cls.emptyBase)
            rs = Test().root
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
        status = base.StatusTestCase().root
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
                root.append(Test().root)
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
