# coding: utf-8
""" Unit tests for models.billpay.recur """
# stdlib imports
import unittest
from decimal import Decimal

import xml.etree.ElementTree as ET


# local imports
from ofxtools.models.billpay.recur import (
    RECPMTRQ,
    RECPMTRS,
    RECPMTMODRQ,
    RECPMTMODRS,
    RECPMTCANCRQ,
    RECPMTCANCRS,
    RECPMTTRNRQ,
    RECPMTTRNRS,
)
from ofxtools.utils import classproperty


# test imports
import base
import test_models_bank_recur as bk_recur
import test_models_billpay_common as bp_common


class RecpmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "PMTINFO"]
    optionalElements = ["INITIALAMT", "FINALAMT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("RECPMTRQ")
        root.append(bk_recur.RecurrinstTestCase.etree)
        root.append(bp_common.PmtinfoTestCase.etree)
        ET.SubElement(root, "INITIALAMT").text = "12.25"
        ET.SubElement(root, "FINALAMT").text = "22.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTRQ(
            recurrinst=bk_recur.RecurrinstTestCase.aggregate,
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
            initialamt=Decimal("12.25"),
            finalamt=Decimal("22.50"),
        )


class RecpmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "PMTINFO"]
    optionalElements = ["INITIALAMT", "FINALAMT", "EXTDPAYEE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("RECPMTRS")
        ET.SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        ET.SubElement(root, "PAYEELSTID").text = "123456"
        ET.SubElement(root, "CURDEF").text = "USD"
        root.append(bk_recur.RecurrinstTestCase.etree)
        root.append(bp_common.PmtinfoTestCase.etree)
        ET.SubElement(root, "INITIALAMT").text = "12.25"
        ET.SubElement(root, "FINALAMT").text = "22.50"
        root.append(bp_common.ExtdpayeeTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTRS(
            recsrvrtid="DEADBEEF",
            payeelstid="123456",
            curdef="USD",
            recurrinst=bk_recur.RecurrinstTestCase.aggregate,
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
            initialamt=Decimal("12.25"),
            finalamt=Decimal("22.50"),
            extdpayee=bp_common.ExtdpayeeTestCase.aggregate,
        )


class RecpmtmodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "PMTINFO", "MODPENDING"]
    optionalElements = ["INITIALAMT", "FINALAMT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("RECPMTMODRQ")
        ET.SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(bk_recur.RecurrinstTestCase.etree)
        root.append(bp_common.PmtinfoTestCase.etree)
        ET.SubElement(root, "INITIALAMT").text = "12.25"
        ET.SubElement(root, "FINALAMT").text = "22.50"
        ET.SubElement(root, "MODPENDING").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTMODRQ(
            recsrvrtid="DEADBEEF",
            recurrinst=bk_recur.RecurrinstTestCase.aggregate,
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
            initialamt=Decimal("12.25"),
            finalamt=Decimal("22.50"),
            modpending=True,
        )


class RecpmtmodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "PMTINFO", "MODPENDING"]
    optionalElements = ["INITIALAMT", "FINALAMT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("RECPMTMODRS")
        ET.SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(bk_recur.RecurrinstTestCase.etree)
        root.append(bp_common.PmtinfoTestCase.etree)
        ET.SubElement(root, "INITIALAMT").text = "12.25"
        ET.SubElement(root, "FINALAMT").text = "22.50"
        ET.SubElement(root, "MODPENDING").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTMODRS(
            recsrvrtid="DEADBEEF",
            recurrinst=bk_recur.RecurrinstTestCase.aggregate,
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
            initialamt=Decimal("12.25"),
            finalamt=Decimal("22.50"),
            modpending=True,
        )


class RecpmtcancrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("RECPMTCANCRQ")
        ET.SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        ET.SubElement(root, "CANPENDING").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTCANCRQ(recsrvrtid="DEADBEEF", canpending=True)


class RecpmtcancrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("RECPMTCANCRS")
        ET.SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        ET.SubElement(root, "CANPENDING").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTCANCRS(recsrvrtid="DEADBEEF", canpending=True)


class RecpmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = RecpmtrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            recpmtrq=RecpmtrqTestCase.aggregate,
        )


class RecpmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = RecpmtrsTestCase

    @classproperty
    @classmethod
    def etree(cls):
        root = cls.emptyBase
        root.append(RecpmtrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return RECPMTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            recpmtrs=RecpmtrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
