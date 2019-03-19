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
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.signup import (
    CLIENTENROLL, WEBENROLL, OTHERENROLL,
    SIGNUPMSGSETV1, SIGNUPMSGSET,
)

from . import base
from . import test_models_common


class ClientenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['ACCTREQUIRED', ]

    @property
    def root(self):
        root = Element('CLIENTENROLL')
        SubElement(root, 'ACCTREQUIRED').text = 'Y'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CLIENTENROLL)
        self.assertEqual(root.acctrequired, True)


class WebenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['URL', ]

    @property
    def root(self):
        root = Element('WEBENROLL')
        SubElement(root, 'URL').text = 'http://www.ameritrade.com'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, WEBENROLL)
        self.assertEqual(root.url, 'http://www.ameritrade.com')


class OtherenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['MESSAGE', ]

    @property
    def root(self):
        root = Element('OTHERENROLL')
        SubElement(root, 'MESSAGE').text = 'Mail me $99.99'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OTHERENROLL)
        self.assertEqual(root.message, 'Mail me $99.99')


class Signupmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['MSGSETCORE', 'CHGUSERINFO', 'AVAILACCTS',
                        'CLIENTACTREQ', ]

    @property
    def root(self):
        root = Element('SIGNUPMSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        enroll = WebenrollTestCase().root
        root.append(enroll)
        SubElement(root, 'CHGUSERINFO').text = 'N'
        SubElement(root, 'AVAILACCTS').text = 'Y'
        SubElement(root, 'CLIENTACTREQ').text = 'N'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNUPMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertIsInstance(root.webenroll, WEBENROLL)
        self.assertEqual(root.chguserinfo, False)
        self.assertEqual(root.availaccts, True)
        self.assertEqual(root.clientactreq, False)


class SignupmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['SIGNUPMSGSETV1', ]

    @property
    def root(self):
        root = Element('SIGNUPMSGSET')
        signup = Signupmsgsetv1TestCase().root
        root.append(signup)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNUPMSGSET)
        self.assertIsInstance(root.signupmsgsetv1, SIGNUPMSGSETV1)
