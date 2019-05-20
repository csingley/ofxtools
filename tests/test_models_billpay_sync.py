# coding: utf-8
""" Unit tests for models.billpay.sync """
# stdlib imports
import unittest
import xml.etree.ElementTree as ET


# local imports
from ofxtools.models.billpay.sync import (
    PMTSYNCRQ,
    PMTSYNCRS,
    RECPMTSYNCRQ,
    RECPMTSYNCRS,
    PAYEESYNCRQ,
    PAYEESYNCRS,
)
from ofxtools.utils import classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt
import test_models_billpay_list as bp_list
import test_models_billpay_pmt as bp_pmt
import test_models_billpay_recur as bp_recur


class PmtsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("PMTSYNCRQ")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(bp_pmt.PmttrnrqTestCase.etree)
        root.append(bp_pmt.PmttrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return PMTSYNCRQ(
            bp_pmt.PmttrnrqTestCase.aggregate,
            bp_pmt.PmttrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bp_pmt.PmttrnrqTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root
            root.append(trnrq)
            root.append(trnrq)
            yield root


class PmtsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    requiredElements = base.SyncrsTestCase.requiredElements + ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("PMTSYNCRS")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(bp_pmt.PmttrnrsTestCase.etree)
        root.append(bp_pmt.PmttrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return PMTSYNCRS(
            bp_pmt.PmttrnrsTestCase.aggregate,
            bp_pmt.PmttrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bp_pmt.PmttrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            yield root
            root.append(trnrs)
            yield root
            root.append(trnrs)
            root.append(trnrs)
            yield root


class RecpmtsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("RECPMTSYNCRQ")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(bp_recur.RecpmttrnrqTestCase.etree)
        root.append(bp_recur.RecpmttrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return RECPMTSYNCRQ(
            bp_recur.RecpmttrnrqTestCase.aggregate,
            bp_recur.RecpmttrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bp_recur.RecpmttrnrqTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root
            root.append(trnrq)
            root.append(trnrq)
            yield root


class RecpmtsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    requiredElements = base.SyncrsTestCase.requiredElements + ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("RECPMTSYNCRS")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(bp_recur.RecpmttrnrsTestCase.etree)
        root.append(bp_recur.RecpmttrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return RECPMTSYNCRS(
            bp_recur.RecpmttrnrsTestCase.aggregate,
            bp_recur.RecpmttrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bp_recur.RecpmttrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            yield root
            root.append(trnrs)
            yield root
            root.append(trnrs)
            root.append(trnrs)
            yield root


class PayeesyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("PAYEESYNCRQ")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bp_list.PayeetrnrqTestCase.etree)
        root.append(bp_list.PayeetrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return PAYEESYNCRQ(
            bp_list.PayeetrnrqTestCase.aggregate,
            bp_list.PayeetrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        trnrq = bp_list.PayeetrnrqTestCase.etree

        for root in super().validSoup:
            root.append(trnrq)
            yield root
            root.append(trnrq)
            root.append(trnrq)
            yield root


class PayeesyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("PAYEESYNCRS")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bp_list.PayeetrnrsTestCase.etree)
        root.append(bp_list.PayeetrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return PAYEESYNCRS(
            bp_list.PayeetrnrsTestCase.aggregate,
            bp_list.PayeetrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        trnrs = bp_list.PayeetrnrsTestCase.etree

        for root in super().validSoup:
            yield root
            root.append(trnrs)
            yield root
            root.append(trnrs)
            root.append(trnrs)
            yield root


if __name__ == "__main__":
    unittest.main()
