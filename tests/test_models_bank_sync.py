# coding: utf-8
"""
Unit tests for models.bank.sync
"""

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy


# local imports
from ofxtools.models.bank.sync import (
    STPCHKSYNCRQ,
    STPCHKSYNCRS,
    INTRASYNCRQ,
    INTRASYNCRS,
    INTERSYNCRQ,
    INTERSYNCRS,
    WIRESYNCRQ,
    WIRESYNCRS,
    BANKMAILSYNCRQ,
    BANKMAILSYNCRS,
    RECINTRASYNCRQ,
    RECINTRASYNCRS,
    RECINTERSYNCRQ,
    RECINTERSYNCRS,
)
from ofxtools.utils import classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt
import test_models_bank_stpchk as stpchk
import test_models_bank_xfer as xfer
import test_models_bank_interxfer as interxfer
import test_models_bank_wire as wire
import test_models_bank_recur as bk_recur
import test_models_bank_mail as bk_mail


class StpchksyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(stpchk.StpchktrnrqTestCase.etree)
        root.append(stpchk.StpchktrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return STPCHKSYNCRQ(
            stpchk.StpchktrnrqTestCase.aggregate,
            stpchk.StpchktrnrqTestCase.aggregate,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        for root in super().validSoup:
            root.append(bk_stmt.BankacctfromTestCase.etree)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(stpchk.StpchktrnrqTestCase.etree)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = stpchk.StpchktrnrqTestCase.etree

        # SYNCRQ base malformed; STPCHK additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            yield root

        # SYNCRQ base OK; STPCHK additions malformed
        for root_ in super().validSoup:
            # BANKACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root_).index(root_.find("REJECTIFMISSING"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, acctfrom)
                yield root

            #  STPCHKTRNRQ in the wrong place
            #  (should be last, right after BANKACCTFROM)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class StpchksyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    requiredElements = base.SyncrsTestCase.requiredElements + ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = Element("STPCHKSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(stpchk.StpchktrnrsTestCase.etree)
        root.append(stpchk.StpchktrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return STPCHKSYNCRS(
            stpchk.StpchktrnrsTestCase.aggregate,
            stpchk.StpchktrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = stpchk.StpchktrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = stpchk.StpchktrnrsTestCase.etree

        # SYNCRS base malformed; STPCHK additions OK
        for root_ in super().invalidSoup:
            root = deepcopy(root_)
            root.append(acctfrom)
            yield root

        # SYNCRS base OK; STPCHK additions malformed
        for root_ in super().validSoup:
            # BANKACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root_).index(root_.find("LOSTSYNC"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, acctfrom)
                yield root

            #  STPCHKTRNRS in the wrong place
            #  (should be right after BANKACCTFROM)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class IntrasyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("INTRASYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return INTRASYNCRQ(
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrq = xfer.IntratrnrqTestCase.etree

        for root_ in super().validSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrq))
                    yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrq = xfer.IntratrnrqTestCase.etree

        # SYNCRQ base malformed; INTRA additions OK
        for root_ in super().invalidSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrq))
                    yield root

        # SYNCRQ base OK; INTRA additions malformed
        for root_ in super().validSoup:
            # *ACCTFROM missing (required)
            yield root_
            # Both BANKACCTFROM and CCACCTFROM (mutex)
            root = deepcopy(root_)
            root.append(bankacctfrom)
            root.append(ccacctfrom)
            yield root

            root = deepcopy(root_)
            root.append(ccacctfrom)
            root.append(bankacctfrom)
            yield root

            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            for acctfrom in (bankacctfrom, ccacctfrom):
                index = list(root_).index(root_.find("REJECTIFMISSING"))
                for n in range(index):
                    root = deepcopy(root_)
                    root.insert(n, acctfrom)
                    yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class IntrasyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("INTRASYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return INTRASYNCRS(
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrs = xfer.IntratrnrsTestCase.etree

        for root_ in super().validSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrs))
                    yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrs = xfer.IntratrnrsTestCase.etree

        # SYNCRS base malformed; INTRA additions OK
        for root_ in super().invalidSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrs))
                    yield root

        # SYNCRS base OK; INTRA additions malformed
        for root_ in super().validSoup:
            # *ACCTFROM missing (required)
            yield root_
            # Both BANKACCTFROM and CCACCTFROM (mutex)
            root = deepcopy(root_)
            root.append(bankacctfrom)
            root.append(ccacctfrom)
            yield root

            root = deepcopy(root_)
            root.append(ccacctfrom)
            root.append(bankacctfrom)
            yield root

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            for acctfrom in (bankacctfrom, ccacctfrom):
                index = list(root_).index(root_.find("LOSTSYNC"))
                for n in range(index):
                    root = deepcopy(root_)
                    root.insert(n, acctfrom)
                    yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class IntersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("INTERSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return INTERSYNCRQ(
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrq = interxfer.IntertrnrqTestCase.etree

        for root_ in super().validSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrq))
                    yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrq = interxfer.IntertrnrqTestCase.etree

        # SYNCRQ base malformed; INTER additions OK
        for root_ in super().invalidSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrq))
                    yield root

        # SYNCRQ base OK; INTER additions malformed
        for root_ in super().validSoup:
            # *ACCTFROM missing (required)
            yield root_
            # Both BANKACCTFROM and CCACCTFROM (mutex)
            root = deepcopy(root_)
            root.append(bankacctfrom)
            root.append(ccacctfrom)
            yield root

            root = deepcopy(root_)
            root.append(ccacctfrom)
            root.append(bankacctfrom)
            yield root

            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            for acctfrom in (bankacctfrom, ccacctfrom):
                index = list(root_).index(root_.find("REJECTIFMISSING"))
                for n in range(index):
                    root = deepcopy(root_)
                    root.insert(n, acctfrom)
                    yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class IntersyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("INTERSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return INTERSYNCRS(
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrs = interxfer.IntertrnrsTestCase.etree

        for root_ in super().validSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrs))
                    yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        bankacctfrom = bk_stmt.BankacctfromTestCase.etree
        ccacctfrom = bk_stmt.CcacctfromTestCase.etree
        trnrs = interxfer.IntertrnrsTestCase.etree

        # SYNCRS base malformed; INTER additions OK
        for root_ in super().invalidSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrs))
                    yield root

        # SYNCRS base OK; INTER additions malformed
        for root_ in super().validSoup:
            # *ACCTFROM missing (required)
            yield root_
            # Both BANKACCTFROM and CCACCTFROM (mutex)
            root = deepcopy(root_)
            root.append(bankacctfrom)
            root.append(ccacctfrom)
            yield root

            root = deepcopy(root_)
            root.append(ccacctfrom)
            root.append(bankacctfrom)
            yield root

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            for acctfrom in (bankacctfrom, ccacctfrom):
                index = list(root_).index(root_.find("LOSTSYNC"))
                for n in range(index):
                    root = deepcopy(root_)
                    root.insert(n, acctfrom)
                    yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class WiresyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = Element("WIRESYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(wire.WiretrnrqTestCase.etree)
        root.append(wire.WiretrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return WIRESYNCRQ(
            wire.WiretrnrqTestCase.aggregate,
            wire.WiretrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = wire.WiretrnrqTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = wire.WiretrnrqTestCase.etree

        # SYNCRQ base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class WiresyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("WIRESYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(wire.WiretrnrsTestCase.etree)
        root.append(wire.WiretrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return WIRESYNCRS(
            wire.WiretrnrsTestCase.aggregate,
            wire.WiretrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = wire.WiretrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = wire.WiretrnrsTestCase.etree

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class RecintrasyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = Element("RECINTRASYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return RECINTRASYNCRQ(
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bk_recur.RecintratrnrqTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bk_recur.RecintratrnrqTestCase.etree

        # SYNCRQ base malformed; RECINTRA additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; RECINTRA additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class RecintrasyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("RECINTRASYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return RECINTRASYNCRS(
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bk_recur.RecintratrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bk_recur.RecintratrnrsTestCase.etree

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class RecintersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @classproperty
    @classmethod
    def etree(self):
        root = Element("RECINTERSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return RECINTERSYNCRQ(
            token="DEADBEEF",
            rejectifmissing=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bk_recur.RecintertrnrqTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bk_recur.RecintertrnrqTestCase.etree

        # SYNCRQ base malformed; RECINTER additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; RECINTER additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class RecintersyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("RECINTERSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return RECINTERSYNCRS(
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bk_recur.RecintertrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bk_recur.RecintertrnrsTestCase.etree

        # SYNCRS base malformed; RECINTER additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; RECINTER additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class BankmailsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + [
        "INCIMAGES",
        "USEHTML",
        "BANKACCTFROM",
    ]

    @classproperty
    @classmethod
    def etree(self):
        root = Element("BANKMAILSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        SubElement(root, "INCIMAGES").text = "Y"
        SubElement(root, "USEHTML").text = "N"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return BANKMAILSYNCRQ(
            token="DEADBEEF",
            rejectifmissing=True,
            incimages=True,
            usehtml=False,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bk_mail.BankmailtrnrqTestCase.etree

        for root in super().validSoup:
            SubElement(root, "INCIMAGES").text = "N"
            SubElement(root, "USEHTML").text = "N"
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrq = bk_mail.BankmailtrnrqTestCase.etree

        # SYNCRQ base malformed; WIRE additions OK
        for root in super().invalidSoup:
            SubElement(root, "INCIMAGES").text = "N"
            SubElement(root, "USEHTML").text = "N"
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrq)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


class BankmailsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = Element("BANKMAILSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return BANKMAILSYNCRS(
            token="DEADBEEF",
            lostsync=True,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bk_mail.BankmailtrnrsTestCase.etree

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @classproperty
    @classmethod
    def invalidSoup(self):
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        trnrs = bk_mail.BankmailtrnrsTestCase.etree

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            index = len(root)
            for n in range(index):
                root = deepcopy(root)
                root.insert(n, trnrs)
                root.append(bk_stmt.BankacctfromTestCase.etree)
                yield root


if __name__ == "__main__":
    unittest.main()
