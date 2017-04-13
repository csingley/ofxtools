# coding: utf-8
""" Unit tests for models/messages.py """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
)


# local imports
from . import common
from . import test_models_base
from . import test_models_lists
from . import test_models_statements

from ofxtools.models import (
    Aggregate, OFX,
    SIGNONMSGSRSV1,
    SECLISTMSGSRSV1,
    BANKMSGSRSV1,
    CREDITCARDMSGSRSV1,
    INVSTMTMSGSRSV1,
    SONRS,
    SECLIST,
    STMTTRNRS,
    INVSTMTTRNRS,
)


class OfxTestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('OFX')
        for msg in (Signonmsgsrsv1TestCase, Bankmsgsrsv1TestCase,
                    Creditcardmsgsrsv1TestCase, Invstmtmsgsrsv1TestCase,
                    Seclistmsgsrsv1TestCase,):
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


class Signonmsgsrsv1TestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    # FIXME
    # requiredElements = ('SONRS',)

    @property
    def root(self):
        root = Element('SIGNONMSGSRSV1')
        sonrs = test_models_base.SonrsTestCase().root
        root.append(sonrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSRSV1)
        self.assertIsInstance(root.sonrs, SONRS)


class Seclistmsgsrsv1TestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    # FIXME
    # requiredElements = ('SECLIST',)

    @property
    def root(self):
        root = Element('SECLISTMSGSRSV1')
        seclist = test_models_lists.SeclistTestCase().root
        root.append(seclist)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSRSV1)
        self.assertIsInstance(root.seclist, SECLIST)


class Bankmsgsrsv1TestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('BANKMSGSRSV1')
        for i in range(2):
            stmttrnrs = test_models_statements.StmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, STMTTRNRS)


class Creditcardmsgsrsv1TestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('CREDITCARDMSGSRSV1')
        for i in range(2):
            stmttrnrs = test_models_statements.StmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, STMTTRNRS)


class Invstmtmsgsrsv1TestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('INVSTMTMSGSRSV1')
        for i in range(2):
            stmttrnrs = test_models_statements.InvstmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, INVSTMTTRNRS)


if __name__ == '__main__':
    unittest.main()
