# coding: utf-8
""" """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from ofxtools.models.base import (
    Aggregate,
)
from ofxtools.models.common import (
    MSGSETCORE,
)
from ofxtools.models.tax1099 import (
    TAX1099MSGSET, TAX1099MSGSETV1,
)

from . import base
from . import test_models_common


class Tax1099msgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    """
    """
    requiredElements = ['MSGSETCORE', 'TAX1099DNLD', 'EXTD1099B',
                        'TAXYEARSUPPORTED', ]

    @property
    def root(self):
        root = Element('TAX1099MSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, 'TAX1099DNLD').text = 'Y'
        SubElement(root, 'EXTD1099B').text = 'Y'
        SubElement(root, 'TAXYEARSUPPORTED').text = '2005'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, TAX1099MSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.tax1099dnld, True)
        self.assertEqual(root.extd1099b, True)
        self.assertEqual(root.taxyearsupported, 2005)


class Tax1099msgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('TAX1099MSGSET')
        msgsetv1 = Tax1099msgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, TAX1099MSGSET)
        self.assertIsInstance(root.tax1099msgsetv1, TAX1099MSGSETV1)


if __name__ == '__main__':
    unittest.main()
