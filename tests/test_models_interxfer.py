# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools
from decimal import Decimal


# local imports
import base
import test_models_common
import test_models_bank

from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.bank import XFERINFO, XFERPRCSTS, XFERPROF, RECURRINST
from ofxtools.models.interxfer import (INTERRQ, INTERRS, INTERMODRQ, INTERMODRS, INTERCANRQ, INTERCANRS, INTERTRNRQ, INTERTRNRS, INTERSYNCRQ, INTERSYNCRS, RECINTERRQ, RECINTERRS, RECINTERMODRQ, RECINTERMODRS, RECINTERCANRQ, RECINTERCANRS, RECINTERTRNRQ, RECINTERTRNRS, RECINTERSYNCRQ, RECINTERSYNCRS, INTERXFERMSGSRQV1, INTERXFERMSGSRSV1, INTERXFERMSGSETV1, INTERXFERMSGSET)
from ofxtools.models.i18n import CURRENCY_CODES


class InterrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERINFO"]

    @property
    def root(self):
        root = Element("INTERRQ")
        xferinfo = test_models_bank.XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERRQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)


class InterrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "XFERINFO"]
    optionalElements = ["REFNUM", "RECSRVRTID", "XFERPRCSTS"]

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
            xferinfo = test_models_bank.XferinfoTestCase().root
            root.append(xferinfo)
            if dtChoice is not None:
                root.append(dtChoice)
            SubElement(root, "REFNUM").text = "B00B135"
            SubElement(root, "RECSRVRTID").text = "B16B00B5"
            xferprcsts = test_models_bank.XferprcstsTestCase().root
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

        root = Element("INTERRS")
        SubElement(root, "CURDEF").text = "EUR"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = test_models_bank.XferinfoTestCase().root
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
        self.oneOfTest('CURDEF', CURRENCY_CODES)


class IntermodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @property
    def root(self):
        root = Element("INTERMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = test_models_bank.XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERMODRQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntercanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("INTERCANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERCANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntermodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @property
    def root(self):
        root = Element("INTERMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = test_models_bank.XferinfoTestCase().root
        root.append(xferinfo)
        xferprcsts = test_models_bank.XferprcstsTestCase().root
        root.append(xferprcsts)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERMODRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertIsInstance(instance.xferprcsts, XFERPRCSTS)


class IntercanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("INTERCANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERCANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntertrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = InterrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in InterrqTestCase, IntermodrqTestCase, IntercanrqTestCase:
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
        for elements in itertools.permutations(legal):
            if elements == legal:
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
                root.append(Test().root)
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

    wraps = InterrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in InterrsTestCase, IntermodrsTestCase, IntercanrsTestCase:
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
        for elements in itertools.permutations(legal):
            if elements == legal:
                continue
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("interrs", "intermodrs", "intercanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTERRS/INTERMODRS/INTERCANRS
        yield root

        # Multiple INTERRS/INTERMODRS/INTERCANRS
        for Tests in [
            (InterrsTestCase, IntermodrsTestCase),
            (InterrsTestCase, IntercanrsTestCase),
            (IntermodrsTestCase, IntercanrsTestCase),
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


class IntersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        ccacctfrom = test_models_bank.CcacctfromTestCase().root
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
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        ccacctfrom = test_models_bank.CcacctfromTestCase().root
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
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        ccacctfrom = test_models_bank.CcacctfromTestCase().root
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
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        ccacctfrom = test_models_bank.CcacctfromTestCase().root
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


class RecinterrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "INTERRQ"]

    @property
    def root(self):
        root = Element("RECINTERRQ")
        root.append(test_models_bank.RecurrinstTestCase().root)
        root.append(InterrqTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERRQ)
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrq, INTERRQ)


class RecinterrsTestCase(unittest.TestCase, base.TestAggregate):

    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRS"]

    @property
    def root(self):
        root = Element("RECINTERRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(test_models_bank.RecurrinstTestCase().root)
        root.append(InterrsTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrs, INTERRS)


class RecintermodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRQ", "MODPENDING"]

    @property
    def root(self):
        root = Element("RECINTERMODRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(test_models_bank.RecurrinstTestCase().root)
        root.append(InterrqTestCase().root)
        SubElement(root, "MODPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERMODRQ)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrq, INTERRQ)
        self.assertEqual(instance.modpending, False)


class RecintermodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRS", "MODPENDING"]

    @property
    def root(self):
        root = Element("RECINTERMODRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(test_models_bank.RecurrinstTestCase().root)
        root.append(InterrsTestCase().root)
        SubElement(root, "MODPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERMODRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrs, INTERRS)
        self.assertEqual(instance.modpending, False)


class RecintercanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @property
    def root(self):
        root = Element("RECINTERCANRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERCANRQ)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertEqual(instance.canpending, False)


class RecintercanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @property
    def root(self):
        root = Element("RECINTERCANRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERCANRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertEqual(instance.canpending, False)


class RecintertrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = RecinterrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase:
            root = cls.emptyBase
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
        for elements in itertools.permutations(legal):
            if elements == legal:
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
            (RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase),
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


class RecintertrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = RecinterrsTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecinterrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase:
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
        for elements in itertools.permutations(legal):
            if elements == legal:
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
            (RecinterrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase),
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


class RecintersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = test_models_bank.BankacctfromTestCase().root
        trnrq = RecintertrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = test_models_bank.BankacctfromTestCase().root
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
        acctfrom = test_models_bank.BankacctfromTestCase().root
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
        acctfrom = test_models_bank.BankacctfromTestCase().root
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


class Interxfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSRQV1")
        for rq in (
            IntertrnrqTestCase,
            RecintertrnrqTestCase,
            IntersyncrqTestCase,
            RecintersyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # INTERXFERMSGSRQV1 may contain
        # ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]
        allowedTags = INTERXFERMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 4)
        root = deepcopy(self.root)
        root.append(IntertrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERXFERMSGSRQV1)
        self.assertEqual(len(instance), 8)
        self.assertIsInstance(instance[0], INTERTRNRQ)
        self.assertIsInstance(instance[1], INTERTRNRQ)
        self.assertIsInstance(instance[2], RECINTERTRNRQ)
        self.assertIsInstance(instance[3], RECINTERTRNRQ)
        self.assertIsInstance(instance[4], INTERSYNCRQ)
        self.assertIsInstance(instance[5], INTERSYNCRQ)
        self.assertIsInstance(instance[6], RECINTERSYNCRQ)
        self.assertIsInstance(instance[7], RECINTERSYNCRQ)


class Interxfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSRSV1")
        for rq in (
            IntertrnrsTestCase,
            RecintertrnrsTestCase,
            IntersyncrsTestCase,
            RecintersyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # INTERXFERMSGSRSV1 may contain
        # ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]
        allowedTags = INTERXFERMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 4)
        root = deepcopy(self.root)
        root.append(IntertrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERXFERMSGSRSV1)
        self.assertEqual(len(instance), 8)
        self.assertIsInstance(instance[0], INTERTRNRS)
        self.assertIsInstance(instance[1], INTERTRNRS)
        self.assertIsInstance(instance[2], RECINTERTRNRS)
        self.assertIsInstance(instance[3], RECINTERTRNRS)
        self.assertIsInstance(instance[4], INTERSYNCRS)
        self.assertIsInstance(instance[5], INTERSYNCRS)
        self.assertIsInstance(instance[6], RECINTERSYNCRS)
        self.assertIsInstance(instance[7], RECINTERSYNCRS)


class Interxfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSETV1")
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        xferprof = test_models_bank.XferprofTestCase().root
        root.append(xferprof)
        SubElement(root, "CANBILLPAY").text = "Y"
        SubElement(root, "CANCWND").text = "2"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INTERXFERMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertIsInstance(root.xferprof, XFERPROF)
        self.assertEqual(root.canbillpay, True)
        self.assertEqual(root.cancwnd, 2)
        self.assertEqual(root.domxferfee, Decimal("7.50"))
        self.assertEqual(root.intlxferfee, Decimal("17.50"))


class InterxfermsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSET")
        msgsetv1 = Interxfermsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INTERXFERMSGSET)
        self.assertIsInstance(root.interxfermsgsetv1, INTERXFERMSGSETV1)


if __name__ == "__main__":
    unittest.main()
