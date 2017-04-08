# coding: utf-8

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import common
from . import test_models_banktransactions
from ofxtools.models import (
    Aggregate,
    STMTTRN,
    BANKTRANLIST, BALLIST,
)


class BanktranlistTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('DTSTART', 'DTEND',)
    optionalElements = ('STMTTRN',)  # FIXME - *ALL* STMTTRN optional!

    @property
    def root(self):
        root = Element('BANKTRANLIST')
        SubElement(root, 'DTSTART').text = '20130601'
        SubElement(root, 'DTEND').text = '20130630'
        for i in range(2):
            stmttrn = test_models_banktransactions.StmttrnTestCase().root
            root.append(stmttrn)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1))
        self.assertEqual(root.dtend, datetime(2013, 6, 30))
        self.assertEqual(len(root), 2)
        for i in range(2):
            self.assertIsInstance(root[i], STMTTRN)


# FIXME - need INVTRAN Elements for list!!!
class InvtranlistTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('DTSTART', 'DTEND',)
    optionalElements = ()  # FIXME - how to handle INVTRAN subclasses?

    @property
    def root(self):
        root = Element('INVTRANLIST')
        SubElement(root, 'DTSTART').text = '20130601'
        SubElement(root, 'DTEND').text = '20130630'
        # FIXME
        # for i in range(2):
            # invtran = test_models_invtransactions.InvtranTestCase().root
            # root.append(invtran)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1))
        self.assertEqual(root.dtend, datetime(2013, 6, 30))
        # FIXME
        # self.assertEqual(len(root), 2)
        # for i in range(2):
            # self.assertIsInstance(root[i], INVTRAN)


if __name__ == '__main__':
    unittest.main()
