# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime, time
from decimal import Decimal
from copy import deepcopy


# local imports
import base
import test_models_common
import test_models_bank

from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.bank.wire import (
    EXTBANKDESC, WIREDESTBANK, WIREBENEFICIARY, WIRERQ, WIRERS, WIRECANRQ,
    WIRECANRS, WIRETRNRQ, WIRETRNRS,
)
from ofxtools.models.bank.sync import WIRESYNCRQ, WIRESYNCRS
from ofxtools.models.bank.msgsets import (
    WIREXFERMSGSRQV1, WIREXFERMSGSRSV1, WIREXFERMSGSETV1, WIREXFERMSGSET,
)
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.utils import UTC


class WirebeneficiaryTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKACCTTO"]
    optionalElements = ["MEMO"]

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element('WIREBENEFICIARY')
        SubElement(root, "NAME").text = "Elmer Fudd"
        root.append(test_models_bank.BankaccttoTestCase().root)
        SubElement(root, "MEMO").text = "For hunting wabbits"
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class ExtbankdescTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKID", "ADDR1", "CITY", "STATE", "POSTALCODE"]
    optionalElements = ["ADDR2", "ADDR3", "COUNTRY", "PHONE"]

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("EXTBANKDESC")
        SubElement(root, "NAME").text = "Lakov Trust"
        SubElement(root, "BANKID").text = "123456789"
        SubElement(root, "ADDR1").text = "123 Main St"
        SubElement(root, "ADDR2").text = "Suite 200"
        SubElement(root, "ADDR3").text = "Attn: Transfer Dept"
        SubElement(root, "CITY").text = "Dime Box"
        SubElement(root, "STATE").text = "TX"
        SubElement(root, "POSTALCODE").text = "77853"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "PHONE").text = "8675309"
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest("COUNTRY", COUNTRY_CODES)


class WiredestbankTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["EXTBANKDESC"]

    @property
    def root(self):
        root = Element("WIREDESTBANK")
        root.append(ExtbankdescTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREDESTBANK)
        self.assertIsInstance(instance.extbankdesc, EXTBANKDESC)


class WirerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "WIREBENEFICIARY", "TRNAMT"]
    optionalElements = ["WIREDESTBANK", "DTDUE", "PAYINSTRUCT"]

    @property
    def root(self):
        root = Element("WIRERQ")
        root.append(test_models_bank.BankacctfromTestCase().root)
        root.append(WirebeneficiaryTestCase().root)
        root.append(WiredestbankTestCase().root)
        SubElement(root, "TRNAMT").text = "123.45"
        SubElement(root, "DTDUE").text = "17760704"
        SubElement(root, "PAYINSTRUCT").text = "Fold until all sharp corners"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIRERQ)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.wirebeneficiary, WIREBENEFICIARY)
        self.assertIsInstance(instance.wiredestbank, WIREDESTBANK)
        self.assertEqual(instance.trnamt, Decimal("123.45"))
        self.assertEqual(instance.dtdue, datetime(1776, 7, 4, tzinfo=UTC))
        self.assertEqual(instance.payinstruct, "Fold until all sharp corners")


class WirersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "BANKACCTFROM", "WIREBENEFICIARY", "TRNAMT"]
    optionalElements = ["WIREDESTBANK", "DTDUE", "PAYINSTRUCT", "FEE", "CONFMSG"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("WIRERS")
        SubElement(root, "CURDEF").text = "USD"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(test_models_bank.BankacctfromTestCase().root)
        root.append(WirebeneficiaryTestCase().root)
        root.append(WiredestbankTestCase().root)
        SubElement(root, "TRNAMT").text = "123.45"
        SubElement(root, "DTDUE").text = "17760704"
        SubElement(root, "PAYINSTRUCT").text = "Fold until all sharp corners"

        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "17760704"

        dtposted = Element("DTPOSTED")
        dtposted.text = "17760704"

        for dtChoice in dtxferprj, dtposted:
            root = cls.emptyBase
            root.append(dtChoice)
            SubElement(root, "FEE").text = "123.45"
            SubElement(root, "CONFMSG").text = "You're good!"

            yield root

        # Opional mutex
        yield cls.emptyBase

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "17760704"

        dtposted = Element("DTPOSTED")
        dtposted.text = "17760704"

        # Mutex
        root = cls.emptyBase
        root.append(dtxferprj)
        root.append(dtposted)
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class WirecanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("WIRECANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIRECANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class WirecanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("WIRECANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIRECANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class WiretrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = WirerqTestCase


class WiretrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = WirersTestCase


class WiresyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = test_models_bank.BankacctfromTestCase().root
        trnrq = WiretrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = test_models_bank.BankacctfromTestCase().root
        trnrq = test_models_bank.IntratrnrsTestCase().root

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
        acctfrom = test_models_bank.BankacctfromTestCase().root
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
        acctfrom = test_models_bank.BankacctfromTestCase().root
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


class Wirexfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRQV1")
        for rq in (
            WiretrnrqTestCase,
            WiresyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # WIREXFERMSGSRQV1 may contain
        # ["WIRETRNRQ", "WIREERSYNCRQ"]
        allowedTags = WIREXFERMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 2)
        root = deepcopy(self.root)
        root.append(WiretrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREXFERMSGSRQV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], WIRETRNRQ)
        self.assertIsInstance(instance[1], WIRETRNRQ)
        self.assertIsInstance(instance[2], WIRESYNCRQ)
        self.assertIsInstance(instance[3], WIRESYNCRQ)


class Wirexfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRSV1")
        for rq in (
            WiretrnrsTestCase,
            WiresyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # WIRERXFERMSGSRSV1 may contain
        # ["WIRETRNRS", "WIRESYNCRS"]
        allowedTags = WIREXFERMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 2)
        root = deepcopy(self.root)
        root.append(WiretrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREXFERMSGSRSV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], WIRETRNRS)
        self.assertIsInstance(instance[1], WIRETRNRS)
        self.assertIsInstance(instance[2], WIRESYNCRS)
        self.assertIsInstance(instance[3], WIRESYNCRS)


class Wirexfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSETV1")
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, WIREXFERMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertIsNone(root.procdaysoff)  # Unsupported
        self.assertEqual(root.procendtm, time(17, 0, 0, tzinfo=UTC))
        self.assertEqual(root.cansched, True)
        self.assertEqual(root.domxferfee, Decimal("7.50"))
        self.assertEqual(root.intlxferfee, Decimal("17.50"))


class WirexfermsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSET")
        msgsetv1 = Wirexfermsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, WIREXFERMSGSET)
        self.assertIsInstance(root.wirexfermsgsetv1, WIREXFERMSGSETV1)


if __name__ == "__main__":
    unittest.main()
