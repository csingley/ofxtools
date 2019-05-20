# coding: utf-8
"""
Unit tests for models.bank.recur
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.bank.recur import (
    FREQUENCIES,
    RECURRINST,
    RECINTRARQ,
    RECINTRARS,
    RECINTRATRNRQ,
    RECINTRATRNRS,
    RECINTERRQ,
    RECINTERRS,
    RECINTRAMODRQ,
    RECINTRAMODRS,
    RECINTRACANRQ,
    RECINTRACANRS,
    RECINTERMODRQ,
    RECINTERMODRS,
    RECINTERCANRQ,
    RECINTERCANRS,
    RECINTERTRNRQ,
    RECINTERTRNRS,
)
from ofxtools.utils import classproperty


# test imports
import base
import test_models_bank_xfer as xfer
import test_models_bank_interxfer as interxfer


class RecurrinstTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["FREQ"]
    optionalElements = ["NINSTS"]
    oneOfs = {"FREQ": FREQUENCIES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECURRINST")
        SubElement(root, "NINSTS").text = "3"
        SubElement(root, "FREQ").text = "MONTHLY"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECURRINST(ninsts=3, freq="MONTHLY")


class RecintrarqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "INTRARQ"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTRARQ")
        root.append(RecurrinstTestCase.etree)
        root.append(xfer.IntrarqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRARQ(
            recurrinst=RecurrinstTestCase.aggregate,
            intrarq=xfer.IntrarqTestCase.aggregate,
        )


class RecintrarsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTRARS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTRARS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase.etree)
        root.append(xfer.IntrarsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRARS(
            recsrvrtid="DEADBEEF",
            recurrinst=RecurrinstTestCase.aggregate,
            intrars=xfer.IntrarsTestCase.aggregate,
        )


class RecintramodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTRARQ", "MODPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTRAMODRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase.etree)
        root.append(xfer.IntrarqTestCase.etree)
        SubElement(root, "MODPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRAMODRQ(
            recsrvrtid="DEADBEEF",
            recurrinst=RecurrinstTestCase.aggregate,
            intrarq=xfer.IntrarqTestCase.aggregate,
            modpending=False,
        )


class RecintramodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTRARS", "MODPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTRAMODRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase.etree)
        root.append(xfer.IntrarsTestCase.etree)
        SubElement(root, "MODPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRAMODRS(
            recsrvrtid="DEADBEEF",
            recurrinst=RecurrinstTestCase.aggregate,
            intrars=xfer.IntrarsTestCase.aggregate,
            modpending=False,
        )


class RecintracanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTRACANRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRACANRQ(recsrvrtid="DEADBEEF", canpending=False)


class RecintracanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTRACANRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRACANRS(recsrvrtid="DEADBEEF", canpending=False)


class RecintratrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = RecintrarqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRATRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            recintrarq=RecintrarqTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecintrarqTestCase, RecintramodrqTestCase, RecintracanrqTestCase:
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

        #  requiredMutex= ("recintrarq", "recintramodrq", "recintracanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTRARQ/RECINTRAMODRQ/RECINTRACANRQ
        yield root

        # Multiple RECINTRARQ/RECINTRAMODRQ/RECINTRACANRQ
        for Tests in [
            (RecintrarqTestCase, RecintramodrqTestCase, RecintracanrqTestCase)
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


class RecintratrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = RecintrarsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTRATRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            recintrars=RecintrarsTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecintrarsTestCase, RecintramodrsTestCase, RecintracanrsTestCase:
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

        #  requiredMutex= ("recintrars", "recintramodrs", "recintracanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTRARS/RECINTRAMODRS/RECINTRACANRS
        yield root

        # Multiple RECINTRARS/RECINTRAMODRS/RECINTRACANRS
        for Tests in [
            (RecintrarsTestCase, RecintramodrsTestCase, RecintracanrsTestCase)
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


class RecinterrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "INTERRQ"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTERRQ")
        root.append(RecurrinstTestCase.etree)
        root.append(interxfer.InterrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERRQ(
            recurrinst=RecurrinstTestCase.aggregate,
            interrq=interxfer.InterrqTestCase.aggregate,
        )


class RecinterrsTestCase(unittest.TestCase, base.TestAggregate):

    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTERRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase.etree)
        root.append(interxfer.InterrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERRS(
            recsrvrtid="DEADBEEF",
            recurrinst=RecurrinstTestCase.aggregate,
            interrs=interxfer.InterrsTestCase.aggregate,
        )


class RecintermodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRQ", "MODPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTERMODRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase.etree)
        root.append(interxfer.InterrqTestCase.etree)
        SubElement(root, "MODPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERMODRQ(
            recsrvrtid="DEADBEEF",
            recurrinst=RecurrinstTestCase.aggregate,
            interrq=interxfer.InterrqTestCase.aggregate,
            modpending=False,
        )


class RecintermodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRS", "MODPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTERMODRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase.etree)
        root.append(interxfer.InterrsTestCase.etree)
        SubElement(root, "MODPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERMODRS(
            recsrvrtid="DEADBEEF",
            recurrinst=RecurrinstTestCase.aggregate,
            interrs=interxfer.InterrsTestCase.aggregate,
            modpending=False,
        )


class RecintercanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTERCANRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERCANRQ(recsrvrtid="DEADBEEF", canpending=False)


class RecintercanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("RECINTERCANRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERCANRS(recsrvrtid="DEADBEEF", canpending=False)


class RecintertrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = RecinterrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            recinterrq=RecinterrqTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase:
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

        #  requiredMutex= ("recinterrq", "recintermodrq", "recintercanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTERRQ/RECINTERMODRQ/RECINTERCANRQ
        yield root

        # Multiple RECINTERRQ/RECINTERMODRQ/RECINTERCANRQ
        for Tests in [
            (RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase)
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


class RecintertrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = RecinterrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECINTERTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            recinterrs=RecinterrsTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecinterrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase:
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

        #  requiredMutex= ("recinterrs", "recintermodrs", "recintercanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTERRS/RECINTERMODRS/RECINTERCANRS
        yield root

        # Multiple RECINTERRS/RECINTERMODRS/RECINTERCANRS
        for Tests in [
            (RecinterrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase)
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
