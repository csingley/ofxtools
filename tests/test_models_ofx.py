# coding: utf-8
""" Unit tests for models/messages.py """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
)


# local imports
from ofxtools.models.base import (
    Aggregate,
)
from ofxtools.models.ofx import OFX
from ofxtools.models.signon import SIGNONMSGSRSV1, SONRS
from ofxtools.models.bank import BANKMSGSRSV1, STMTRS
from ofxtools.models.creditcard import CREDITCARDMSGSRSV1, CCSTMTRS
from ofxtools.models.investment import INVSTMTMSGSRSV1, INVSTMTRS
from ofxtools.models.seclist import SECLISTMSGSRSV1, SECLIST

from . import base
from . import test_signon
from . import test_bank
from . import test_creditcard
from . import test_investment
from . import test_seclist


class OfxTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    unsupported = ['emailmsgsrsv1', 'loanmsgsrsv1',
                   'presdirmsgsrsv1', 'presdlvmsgsrsv1',
                   'tax1095msgsrsv1', 'tax1098msgsrsv1', 'tax1099msgsrsv1',
                   'taxw2msgsrsv1',
                  ]

    @property
    def root(self):
        root = Element('OFX')
        for msg in (test_signon.Signonmsgsrsv1TestCase,
                    test_bank.Bankmsgsrsv1TestCase,
                    test_creditcard.Creditcardmsgsrsv1TestCase,
                    test_investment.Invstmtmsgsrsv1TestCase,
                    test_seclist.Seclistmsgsrsv1TestCase,):
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
        unsupported = sorted(list(root.unsupported.keys()))
        self.assertEqual(unsupported, self.unsupported)
        for unsupp in unsupported:
            setattr(root, unsupp, 'FOOBAR')
            self.assertIsNone(getattr(root, unsupp))

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
        self.assertIsInstance(root.statements[3], CCSTMTRS)
        self.assertIsInstance(root.statements[4], INVSTMTRS)
        self.assertIsInstance(root.statements[5], INVSTMTRS)


if __name__ == '__main__':
    unittest.main()
