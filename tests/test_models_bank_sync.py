# coding: utf-8
"""
Unit tests for models.bank.sync
"""

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate


# test imports
import base
from test_models_bank_stmt import BankacctfromTestCase, CcacctfromTestCase
from test_models_bank_stpchk import StpchktrnrqTestCase, StpchktrnrsTestCase
from test_models_bank_xfer import IntratrnrqTestCase, IntratrnrsTestCase
from test_models_bank_interxfer import IntertrnrqTestCase, IntertrnrsTestCase
from test_models_bank_wire import WiretrnrqTestCase, WiretrnrsTestCase
from test_models_bank_recur import RecintratrnrqTestCase, RecintratrnrsTestCase
from test_models_bank_recur import RecintertrnrqTestCase, RecintertrnrsTestCase
from test_models_bank_mail import BankmailtrnrqTestCase, BankmailtrnrsTestCase


class StpchksyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = StpchktrnrqTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            root.append(deepcopy(acctfrom))
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrq))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        #  trnrq = StpchktrnrqTestCase().root

        # SYNCRQ base malformed; STPCHK additions OK
        for root_ in super().invalidSoup:
            root = deepcopy(root_)
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
            #  (should be right after BANKACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class StpchksyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    requiredElements = base.SyncrsTestCase.requiredElements + ["BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = StpchktrnrsTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            root.append(deepcopy(acctfrom))
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        #  trnrs = StpchktrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class IntrasyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntratrnrqTestCase().root

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

    @property
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntratrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class IntrasyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntratrnrsTestCase().root

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

    @property
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntratrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class IntersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntertrnrqTestCase().root

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

    @property
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntertrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class IntersyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntertrnrsTestCase().root

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

    @property
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntertrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class WiresyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = WiretrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = IntratrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class WiresyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = WiretrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = WiretrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecintrasyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintratrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintratrnrqTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecintrasyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintratrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintratrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecintersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintertrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintertrnrqTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecintersyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintertrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintertrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class BankmailsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + [
        "INCIMAGES",
        "USEHTML",
        "BANKACCTFROM",
    ]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = BankmailtrnrqTestCase().root

        for root in super().validSoup:
            SubElement(root, "INCIMAGES").text = "N"
            SubElement(root, "USEHTML").text = "N"
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = IntratrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class BankmailsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = BankmailtrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = BankmailtrnrsTestCase().root

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
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


if __name__ == "__main__":
    unittest.main()
