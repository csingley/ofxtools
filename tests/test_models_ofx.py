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
from ofxtools.models.signon import SIGNONMSGSRSV1
from ofxtools.models.bank import BANKMSGSRSV1
from ofxtools.models.creditcard import CREDITCARDMSGSRSV1
from ofxtools.models.investment import INVSTMTMSGSRSV1
from ofxtools.models.seclist import SECLISTMSGSRSV1

from . import base
from . import test_signon
from . import test_bank
from . import test_creditcard
from . import test_investment
from . import test_seclist


class OfxTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

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


if __name__ == '__main__':
    unittest.main()
