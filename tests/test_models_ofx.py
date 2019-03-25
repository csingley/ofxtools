# coding: utf-8
""" Unit tests for models/messages.py """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element
from datetime import datetime


# local imports
import base
import test_models_signon
import test_models_bank
import test_models_creditcard
import test_models_investment
import test_models_seclist

from ofxtools.models.base import Aggregate
from ofxtools.models.ofx import OFX
from ofxtools.models.signon import SIGNONMSGSRSV1, SONRS
from ofxtools.models.bank import BANKMSGSRSV1, STMTRS
from ofxtools.models.creditcard import CREDITCARDMSGSRSV1, CCSTMTRS, CCSTMTENDRS
from ofxtools.models.investment import INVSTMTMSGSRSV1, INVSTMTRS
from ofxtools.models.seclist import SECLISTMSGSRSV1, SECLIST

from ofxtools.utils import UTC


class OfxTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    unsupported = [
        "interxfermsgsrqv1",
        "interxfermsgsrsv1",
        "wirexfermsgsrqv1",
        "wirexfermsgsrsv1",
        "billpaymsgsrqv1",
        "billpaymsgsrsv1",
        "emailmsgsrqv1",
        "emailmsgsrsv1",
        "presdirmsgsrqv1",
        "presdirmsgsrsv1",
        "presdlvmsgsrqv1",
        "presdlvmsgsrsv1",
        "loanmsgsrqv1",
        "loanmsgsrsv1",
        "tax1098msgsrqv1",
        "tax1098msgsrsv1",
        "tax1099msgsrqv1",
        "tax1099msgsrsv1",
        "taxw2msgsrqv1",
        "taxw2msgsrsv1",
        "tax1095msgsrqv1",
        "tax1095msgsrsv1",
    ]

    @property
    def root(self):
        root = Element("OFX")
        for msg in (
            test_models_signon.Signonmsgsrsv1TestCase,
            test_models_bank.Bankmsgsrsv1TestCase,
            test_models_creditcard.Creditcardmsgsrsv1TestCase,
            test_models_investment.Invstmtmsgsrsv1TestCase,
            test_models_seclist.Seclistmsgsrsv1TestCase,
        ):
            root.append(msg().root)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OFX)
        self.assertIsInstance(root.signonmsgsrsv1, SIGNONMSGSRSV1)
        self.assertIsInstance(root.bankmsgsrsv1, BANKMSGSRSV1)
        self.assertIsInstance(root.creditcardmsgsrsv1, CREDITCARDMSGSRSV1)
        self.assertIsInstance(root.invstmtmsgsrsv1, INVSTMTMSGSRSV1)
        self.assertIsInstance(root.seclistmsgsrsv1, SECLISTMSGSRSV1)

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        unsupported = list(root.unsupported)
        self.assertEqual(unsupported, self.unsupported)
        for unsupp in unsupported:
            setattr(root, unsupp, "FOOBAR")
            self.assertIsNone(getattr(root, unsupp))

    def testRepr(self):
        agg = Aggregate.from_etree(self.root)
        rep = repr(agg)
        rep_template = (
            "<OFX fid='{fid}' org='{org}' dtserver='{dtserver}' "
            "len(statements)={stmtlen} len(securities)={seclen}>"
        )
        # SIGNON values from test_models_signon.FiTestCase
        # DTSERVER from test_models_signon.SonrsTestCase
        # 2 *STMTs each from bank/cc/invstmt (6 total)
        # 5 securitites from test_models_seclist.SeclistTestCase
        rep_values = {
            "fid": "4705",
            "org": "IBLLC-US",
            "dtserver": datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
            "stmtlen": 6,
            "seclen": 5,
        }
        self.assertEqual(rep, rep_template.format(**rep_values))

    def testPropertyAliases(self):
        # Make sure class property aliases have been defined correctly
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.sonrs, SONRS)
        self.assertIsInstance(root.securities, SECLIST)
        self.assertIsInstance(root.statements, list)
        # *MSGSRSV1 test cases include 2 of each *STMTRS
        self.assertEqual(len(root.statements), 6)
        self.assertIsInstance(root.statements[0], STMTRS)
        self.assertIsInstance(root.statements[1], STMTRS)
        self.assertIsInstance(root.statements[2], CCSTMTRS)
        self.assertIsInstance(root.statements[3], CCSTMTENDRS)
        self.assertIsInstance(root.statements[4], INVSTMTRS)
        self.assertIsInstance(root.statements[5], INVSTMTRS)


if __name__ == "__main__":
    unittest.main()
