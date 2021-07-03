# coding: utf-8
"""
Unit tests for models.bank.interxfer
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
import base
from ofxtools.models.bank.interxfer import (
    INTERRQ,
    INTERRS,
    INTERMODRQ,
    INTERMODRS,
    INTERCANRQ,
    INTERCANRS,
    INTERTRNRQ,
    INTERTRNRS,
)
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import classproperty


# test imports
import test_models_bank_xfer as xfer


class InterrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERRQ")
        root.append(xfer.XferinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERRQ(xferinfo=xfer.XferinfoTestCase.aggregate)


class InterrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "XFERINFO"]
    optionalElements = ["REFNUM", "RECSRVRTID", "XFERPRCSTS"]
    oneOfs = {"CURDEF": CURRENCY_CODES}

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        for dtChoice in (None, dtxferprj, dtposted):
            root = Element("INTERRS")
            SubElement(root, "CURDEF").text = "EUR"
            SubElement(root, "SRVRTID").text = "DEADBEEF"
            root.append(xfer.XferinfoTestCase.etree)
            if dtChoice is not None:
                root.append(dtChoice)
            SubElement(root, "REFNUM").text = "B00B135"
            SubElement(root, "RECSRVRTID").text = "B16B00B5"
            root.append(xfer.XferprcstsTestCase.etree)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [("dtxferprj", "dtposted")]
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        root = Element("INTERRS")
        SubElement(root, "CURDEF").text = "EUR"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = xfer.XferinfoTestCase.etree
        root.append(xferinfo)
        root.append(dtxferprj)
        root.append(dtposted)

        yield root

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERRS(
            curdef="EUR",
            srvrtid="DEADBEEF",
            xferinfo=xfer.XferinfoTestCase.aggregate,
            refnum="B00B135",
            recsrvrtid="B16B00B5",
            xferprcsts=xfer.XferprcstsTestCase.aggregate,
        )


class IntermodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(xfer.XferinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERMODRQ(srvrtid="DEADBEEF", xferinfo=xfer.XferinfoTestCase.aggregate)


class IntercanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERCANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERCANRQ(srvrtid="DEADBEEF")


class IntermodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(xfer.XferinfoTestCase.etree)
        root.append(xfer.XferprcstsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERMODRS(
            srvrtid="DEADBEEF",
            xferinfo=xfer.XferinfoTestCase.aggregate,
            xferprcsts=xfer.XferprcstsTestCase.aggregate,
        )


class IntercanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERCANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERCANRS(srvrtid="DEADBEEF")


class IntertrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = InterrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            interrq=InterrqTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in InterrqTestCase, IntermodrqTestCase, IntercanrqTestCase:
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

        #  requiredMutex= ("interrq", "intermodrq", "intercanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTERRQ/INTERMODRQ/INTERCANRQ
        yield root

        # Multiple INTERRQ/INTERMODRQ/INTERCANRQ
        for Tests in [
            (InterrqTestCase, IntermodrqTestCase),
            (InterrqTestCase, IntercanrqTestCase),
            (IntermodrqTestCase, IntercanrqTestCase),
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


class IntertrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = InterrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            interrs=InterrsTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in InterrsTestCase, IntermodrsTestCase, IntercanrsTestCase:
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

        #  requiredMutex= ("interrs", "intermodrs", "intercanrs")
        root = cls.emptyBase

        # Multiple INTERRS/INTERMODRS/INTERCANRS
        for Tests in [
            (InterrsTestCase, IntermodrsTestCase),
            (InterrsTestCase, IntercanrsTestCase),
            (IntermodrsTestCase, IntercanrsTestCase),
        ]:
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
