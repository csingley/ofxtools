# coding: utf-8
""" Unit tests for models.billpay.pmt """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.billpay.pmt import (
    PMTRQ,
    PMTRS,
    PMTMODRQ,
    PMTMODRS,
    PMTCANCRQ,
    PMTCANCRS,
    PMTTRNRQ,
    PMTTRNRS,
    PMTINQRQ,
    PMTINQRS,
    PMTINQTRNRQ,
    PMTINQTRNRS,
)
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import classproperty


# test imports
import base
import test_models_billpay_common as bp_common


class PmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PMTINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTRQ")
        root.append(bp_common.PmtinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTRQ(pmtinfo=bp_common.PmtinfoTestCase.aggregate)


class PmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PAYEELSTID", "CURDEF", "PMTINFO", "PMTPRCSTS"]
    oneOfs = {"CURDEF": CURRENCY_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        SubElement(root, "PAYEELSTID").text = "B16B00B5"
        SubElement(root, "CURDEF").text = "GBP"
        root.append(bp_common.PmtinfoTestCase.etree)
        root.append(bp_common.ExtdpayeeTestCase.etree)
        SubElement(root, "CHECKNUM").text = "215"
        root.append(bp_common.PmtprcstsTestCase.etree)
        SubElement(root, "RECSRVRTID").text = "B00B135"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTRS(
            srvrtid="DEADBEEF",
            payeelstid="B16B00B5",
            curdef="GBP",
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
            extdpayee=bp_common.ExtdpayeeTestCase.aggregate,
            checknum="215",
            pmtprcsts=bp_common.PmtprcstsTestCase.aggregate,
            recsrvrtid="B00B135",
        )


class PmtmodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PMTINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(bp_common.PmtinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTMODRQ(srvrtid="DEADBEEF", pmtinfo=bp_common.PmtinfoTestCase.aggregate)


class PmtmodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PMTINFO"]
    optionalElements = ["PMTPRCSTS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(bp_common.PmtinfoTestCase.etree)
        root.append(bp_common.PmtprcstsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTMODRS(
            srvrtid="DEADBEEF",
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
            pmtprcsts=bp_common.PmtprcstsTestCase.aggregate,
        )


class PmtcancrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTCANCRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTCANCRQ(srvrtid="DEADBEEF")


class PmtcancrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTCANCRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTCANCRS(srvrtid="DEADBEEF")


class PmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PmtrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            pmtrq=PmtrqTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in PmtrqTestCase, PmtmodrqTestCase, PmtcancrqTestCase:
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
            root = Element(tag)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("pmtrq", "pmtmodrq", "pmtcancrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing PMTRQ/PMTMODRQ/PMTCANCRQ
        yield root

        # Multiple PMTRQ/PMTMODRQ/PMTCANCRQ
        for Tests in [
            (PmtrqTestCase, PmtmodrqTestCase),
            (PmtrqTestCase, PmtcancrqTestCase),
            (PmtmodrqTestCase, PmtcancrqTestCase),
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


class PmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PmtrsTestCase

    @classproperty
    @classmethod
    def etree(cls):
        root = cls.emptyBase
        root.append(PmtrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            pmtrs=PmtrsTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        # Empty *RS is OK
        yield cls.emptyBase

        for Test in PmtrsTestCase, PmtmodrsTestCase, PmtcancrsTestCase:
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

        #  requiredMutex= ("pmtrs", "pmtmodrs", "pmtcancrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing PMTRS/PMTMODRS/PMTCANCRS
        yield root

        # Multiple PMTRS/PMTMODRS/PMTCANCRS
        for Tests in [
            (PmtrsTestCase, PmtmodrsTestCase),
            (PmtrsTestCase, PmtcancrsTestCase),
            (PmtmodrsTestCase, PmtcancrsTestCase),
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


class PmtinqrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTINQRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTINQRQ(srvrtid="DEADBEEF")


class PmtinqrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PMTPRCSTS"]
    optionalElements = ["CHECKNUM"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PMTINQRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(bp_common.PmtprcstsTestCase.etree)
        SubElement(root, "CHECKNUM").text = "215"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTINQRS(
            srvrtid="DEADBEEF",
            pmtprcsts=bp_common.PmtprcstsTestCase.aggregate,
            checknum="215",
        )


class PmtinqtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PmtinqrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTINQTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            pmtinqrq=PmtinqrqTestCase.aggregate,
        )


class PmtinqtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PmtinqrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTINQTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            pmtinqrs=PmtinqrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
