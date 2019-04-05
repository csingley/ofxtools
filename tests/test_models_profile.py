# coding: utf-8
""" """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy


# local imports
import base
import test_models_common
import test_models_signon
import test_models_signup
import test_models_bank
import test_models_creditcard
import test_models_investment
import test_models_seclist
import test_models_tax1099

from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.common import STATUS, MSGSETCORE
from ofxtools.models.profile import (
    PROFRQ,
    PROFRS,
    PROFTRNRQ,
    PROFTRNRS,
    MSGSETLIST,
    PROFMSGSRQV1,
    PROFMSGSRSV1,
    PROFMSGSETV1,
    PROFMSGSET,
)
from ofxtools.models.signon import SIGNONMSGSET, SIGNONINFOLIST
from ofxtools.models.signup import SIGNUPMSGSET
from ofxtools.models.bank import (BANKMSGSET, CREDITCARDMSGSET)
from ofxtools.models.investment import INVSTMTMSGSET
from ofxtools.models.seclist import SECLISTMSGSET
from ofxtools.models.tax1099 import TAX1099MSGSET
from ofxtools.utils import UTC


class ProfrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CLIENTROUTING", "DTPROFUP"]

    @property
    def root(self):
        root = Element("PROFRQ")
        SubElement(root, "CLIENTROUTING").text = "SERVICE"
        SubElement(root, "DTPROFUP").text = "20010401"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFRQ)
        self.assertEqual(root.clientrouting, "SERVICE")
        self.assertEqual(root.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest("CLIENTROUTING", ("NONE", "SERVICE", "MSGSET"))


class ProftrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = ProfrqTestCase


class MsgsetlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("MSGSETLIST")
        signon = test_models_signon.SignonmsgsetTestCase().root
        root.append(signon)
        signup = test_models_signup.SignupmsgsetTestCase().root
        root.append(signup)
        bankmsgset = ProfmsgsetTestCase().root
        root.append(bankmsgset)
        bankmsgset = test_models_bank.BankmsgsetTestCase().root
        root.append(bankmsgset)
        creditcardmsgset = test_models_creditcard.CreditcardmsgsetTestCase().root
        root.append(creditcardmsgset)
        invstmtmsgset = test_models_investment.InvstmtmsgsetTestCase().root
        root.append(invstmtmsgset)
        seclistmsgset = test_models_seclist.SeclistmsgsetTestCase().root
        root.append(seclistmsgset)
        tax1099msgset = test_models_tax1099.Tax1099msgsetTestCase().root
        root.append(tax1099msgset)
        return root

    def testdataTags(self):
        # MSGSETLIST may only contain
        # ["SIGNONMSGSET", "SIGNUPMSGSET", "PROFMSGSET", "BANKMSGSET",
        # "CREDITCARDMSGSET", "INTERXFERMSGSET", "WIREXFERMSGSET",
        # "INVSTMTMSGSET", "SECLISTMSGSET", "BILLPAYMSGSET", "PRESDIRMSGSET",
        # "PRESDLVMSGSET", "TAX1099MSGSET"]
        allowedTags = MSGSETLIST.dataTags
        self.assertEqual(len(allowedTags), 13)
        root = deepcopy(self.root)
        root.append(test_models_bank.StmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        # Test MSGSETLIST wrapper.  *MSGSET members are tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MSGSETLIST)
        self.assertEqual(len(root), 8)
        self.assertIsInstance(root[0], SIGNONMSGSET)
        self.assertIsInstance(root[1], SIGNUPMSGSET)
        self.assertIsInstance(root[2], PROFMSGSET)
        self.assertIsInstance(root[3], BANKMSGSET)
        self.assertIsInstance(root[4], CREDITCARDMSGSET)
        self.assertIsInstance(root[5], INVSTMTMSGSET)
        self.assertIsInstance(root[6], SECLISTMSGSET)
        self.assertIsInstance(root[7], TAX1099MSGSET)


class ProfrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "MSGSETLIST",
        "SIGNONINFOLIST",
        "DTPROFUP",
        "FINAME",
        "ADDR1",
        "CITY",
        "STATE",
        "POSTALCODE",
        "COUNTRY",
    ]
    optionalElements = [
        "ADDR2",
        "ADDR3",
        "CSPHONE",
        "TSPHONE",
        "FAXPHONE",
        "URL",
        "EMAIL",
    ]

    @property
    def root(self):
        root = Element("PROFRS")
        msgsetlist = MsgsetlistTestCase().root
        root.append(msgsetlist)
        signoninfolist = test_models_signon.SignoninfolistTestCase().root
        root.append(signoninfolist)
        SubElement(root, "DTPROFUP").text = "20010401"
        SubElement(root, "FINAME").text = "Dewey Cheatham & Howe"
        SubElement(root, "ADDR1").text = "3717 N Clark St"
        SubElement(root, "ADDR2").text = "Dugout Box, Aisle 19"
        SubElement(root, "ADDR3").text = "Seat A1"
        SubElement(root, "CITY").text = "Chicago"
        SubElement(root, "STATE").text = "IL"
        SubElement(root, "POSTALCODE").text = "60613"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "CSPHONE").text = "(773) 309-1027"
        SubElement(root, "TSPHONE").text = "(773) 309-1028"
        SubElement(root, "FAXPHONE").text = "(773) 309-1029"
        SubElement(root, "URL").text = "http://www.ameritrade.com"
        SubElement(root, "EMAIL").text = "support@ameritrade.com"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFRS)
        self.assertIsInstance(root.msgsetlist, MSGSETLIST)
        self.assertIsInstance(root.signoninfolist, SIGNONINFOLIST)
        self.assertEqual(root.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))
        self.assertEqual(root.finame, "Dewey Cheatham & Howe")
        self.assertEqual(root.addr1, "3717 N Clark St")
        self.assertEqual(root.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(root.addr3, "Seat A1")
        self.assertEqual(root.city, "Chicago")
        self.assertEqual(root.state, "IL")
        self.assertEqual(root.postalcode, "60613")
        self.assertEqual(root.country, "USA")
        self.assertEqual(root.csphone, "(773) 309-1027")
        self.assertEqual(root.tsphone, "(773) 309-1028")
        self.assertEqual(root.faxphone, "(773) 309-1029")
        self.assertEqual(root.url, "http://www.ameritrade.com")
        self.assertEqual(root.email, "support@ameritrade.com")

    def testConvertRemoveProprietaryTag(self):
        # Make sure SONRS.from_etree() removes proprietary tags
        root = deepcopy(self.root)
        SubElement(root, "INTU.BANKID").text = "12345678"

        profrs = Aggregate.from_etree(root)
        self.assertIsInstance(profrs, PROFRS)
        # Converted Aggregate should still have 16 values, not 17
        self.assertEqual(len(profrs._spec_repr), 16)

        self.assertIsInstance(profrs.msgsetlist, MSGSETLIST)
        self.assertIsInstance(profrs.signoninfolist, SIGNONINFOLIST)
        self.assertEqual(profrs.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))
        self.assertEqual(profrs.finame, "Dewey Cheatham & Howe")
        self.assertEqual(profrs.addr1, "3717 N Clark St")
        self.assertEqual(profrs.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(profrs.addr3, "Seat A1")
        self.assertEqual(profrs.city, "Chicago")
        self.assertEqual(profrs.state, "IL")
        self.assertEqual(profrs.postalcode, "60613")
        self.assertEqual(profrs.country, "USA")
        self.assertEqual(profrs.csphone, "(773) 309-1027")
        self.assertEqual(profrs.tsphone, "(773) 309-1028")
        self.assertEqual(profrs.faxphone, "(773) 309-1029")
        self.assertEqual(profrs.url, "http://www.ameritrade.com")
        self.assertEqual(profrs.email, "support@ameritrade.com")


class ProftrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ProfrsTestCase

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        profile = instance.profile
        self.assertIsInstance(profile, PROFRS)


class Profmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PROFMSGSRQV1")
        for i in range(2):
            proftrnrq = ProftrnrqTestCase().root
            root.append(proftrnrq)
        return root

    def testdataTags(self):
        # PROFMSGSRQV1 may only contain PROFTRNRQ
        allowedTags = PROFMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(ProftrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSRQV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, PROFTRNRQ)


class Profmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PROFMSGSRSV1")
        for i in range(2):
            proftrnrs = ProftrnrsTestCase().root
            root.append(proftrnrs)
        return root

    def testdataTags(self):
        # PROFMSGSRSV1 may only contain PROFTRNRS
        allowedTags = PROFMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(ProftrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, PROFTRNRS)


class Profmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE"]

    @property
    def root(self):
        root = Element("PROFMSGSETV1")
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)


class ProfmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PROFMSGSET")
        msgsetv1 = Profmsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSET)
        self.assertIsInstance(root.profmsgsetv1, PROFMSGSETV1)


if __name__ == "__main__":
    unittest.main()
