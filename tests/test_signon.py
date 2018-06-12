# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from datetime import datetime


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import (STATUS, MSGSETCORE)
from ofxtools.models.signon import (
    FI, SONRQ, SONRS, SIGNONMSGSRSV1, SIGNONMSGSETV1, SIGNONMSGSET,
    SIGNONINFO, SIGNONINFOLIST,
)
from ofxtools.models.i18n import LANG_CODES
from ofxtools.utils import UTC

from . import base
from . import test_models_common


class FiTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    optionalElements = ('FID',)

    @property
    def root(self):
        root = Element('FI')
        SubElement(root, 'ORG').text = 'IBLLC-US'
        SubElement(root, 'FID').text = '4705'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FI)
        self.assertEqual(root.org, 'IBLLC-US')
        self.assertEqual(root.fid, '4705')


class SonrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['DTCLIENT', 'LANGUAGE', 'APPID', 'APPVER', ]
    optionalElements = ['FI', 'USERKEY', 'GENUSERKEY', 'SESSCOOKIE', 'APPKEY',
                        'CLIENTUID', 'USERCRED1', 'USERCRED2', 'AUTHTOKEN',
                        'ACCESSKEY', ]

    @property
    def root(self):
        root = Element('SONRQ')
        SubElement(root, 'DTCLIENT').text = '20051029101003'
        SubElement(root, 'USERKEY').text = 'DEADBEEF'
        SubElement(root, 'GENUSERKEY').text = 'N'
        SubElement(root, 'LANGUAGE').text = 'ENG'
        fi = FiTestCase().root
        root.append(fi)
        SubElement(root, 'SESSCOOKIE').text = 'BADA55'
        SubElement(root, 'APPID').text = 'QWIN'
        SubElement(root, 'APPVER').text = '1500'
        SubElement(root, 'APPKEY').text = 'CAFEBABE'
        SubElement(root, 'CLIENTUID').text = 'DEADBEEF'
        SubElement(root, 'USERCRED1').text = 'Something'
        SubElement(root, 'USERCRED2').text = 'Something else'
        SubElement(root, 'AUTHTOKEN').text = 'line noise'
        SubElement(root, 'ACCESSKEY').text = 'CAFEBABE'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRQ)
        self.assertEqual(root.dtclient, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        self.assertEqual(root.userkey, 'DEADBEEF')
        self.assertEqual(root.genuserkey, False)
        self.assertEqual(root.language, 'ENG')
        self.assertIsInstance(root.fi, FI)
        self.assertEqual(root.sesscookie, 'BADA55')
        self.assertEqual(root.appid, 'QWIN')
        self.assertEqual(root.appver, '1500')
        self.assertEqual(root.clientuid, 'DEADBEEF')
        self.assertEqual(root.usercred1, 'Something')
        self.assertEqual(root.usercred2, 'Something else')
        self.assertEqual(root.authtoken, 'line noise')
        self.assertEqual(root.accesskey, 'CAFEBABE')

    def testOneOf(self):
        self.oneOfTest('LANGUAGE', LANG_CODES)


class SonrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('STATUS', 'DTSERVER',)
    optionalElements = ('USERKEY', 'TSKEYEXPIRE', 'DTPROFUP', 'DTACCTUP', 'FI',
                        'SESSCOOKIE', 'ACCESSKEY')

    @property
    def root(self):
        root = Element('SONRS')
        status = test_models_common.StatusTestCase().root
        root.append(status)
        SubElement(root, 'DTSERVER').text = '20051029101003'
        SubElement(root, 'USERKEY').text = 'DEADBEEF'
        SubElement(root, 'TSKEYEXPIRE').text = '20051231'
        SubElement(root, 'LANGUAGE').text = 'ENG'
        SubElement(root, 'DTPROFUP').text = '20050101'
        SubElement(root, 'DTACCTUP').text = '20050102'
        fi = FiTestCase().root
        root.append(fi)
        SubElement(root, 'SESSCOOKIE').text = 'BADA55'
        SubElement(root, 'ACCESSKEY').text = 'CAFEBABE'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRS)
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.dtserver, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        self.assertEqual(root.userkey, 'DEADBEEF')
        self.assertEqual(root.tskeyexpire, datetime(2005, 12, 31, tzinfo=UTC))
        self.assertEqual(root.language, 'ENG')
        self.assertEqual(root.dtprofup, datetime(2005, 1, 1, tzinfo=UTC))
        self.assertEqual(root.dtacctup, datetime(2005, 1, 2, tzinfo=UTC))
        self.assertIsInstance(root.fi, FI)
        self.assertEqual(root.sesscookie, 'BADA55')
        self.assertEqual(root.accesskey, 'CAFEBABE')

    def testOneOf(self):
        self.oneOfTest('LANGUAGE', LANG_CODES)


class Signonmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNONMSGSRSV1')
        sonrs = SonrsTestCase().root
        root.append(sonrs)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSRSV1)
        self.assertIsInstance(root.sonrs, SONRS)


class SignoninfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['SIGNONREALM', 'MIN', 'MAX', 'CHARTYPE', 'CASESEN',
                        'SPECIAL', 'SPACES', 'PINCH', ]
    # optionalElements = ['CHGPINFIRST', 'USERCRED1LABEL', 'USERCRED2LABEL',
                        # 'CLIENTUIDREQ', 'AUTHTOKENFIRST', 'AUTHTOKENLABEL',
                        # 'AUTHTOKENINFOURL', 'MFACHALLENGESUPT',
                        # 'MFACHALLENGEFIRST', 'ACCESSTOKENREQ', ]

    @property
    def root(self):
        root = Element('SIGNONINFO')
        SubElement(root, 'SIGNONREALM').text = 'AMERITRADE'
        SubElement(root, 'MIN').text = '4'
        SubElement(root, 'MAX').text = '32'
        SubElement(root, 'CHARTYPE').text = 'ALPHAORNUMERIC'
        SubElement(root, 'CASESEN').text = 'Y'
        SubElement(root, 'SPECIAL').text = 'N'
        SubElement(root, 'SPACES').text = 'N'
        SubElement(root, 'PINCH').text = 'N'
        SubElement(root, 'CHGPINFIRST').text = 'N'
        # SubElement(root, 'USERCRED1LABEL').text = 'What is your name?'
        # SubElement(root, 'USERCRED2LABEL').text = 'What is your favorite color?'
        # SubElement(root, 'CLIENTUIDREQ').text = 'N'
        # SubElement(root, 'AUTHTOKENFIRST').text = 'Y'
        # SubElement(root, 'AUTHTOKENLABEL').text = 'Enigma'
        # SubElement(root, 'AUTHTOKENINFOURL').text = 'http://www.google.com'
        # SubElement(root, 'MFACHALLENGESUPT').text = 'N'
        # SubElement(root, 'MFACHALLENGEFIRST').text = 'Y'
        # SubElement(root, 'ACCESSTOKENREQ').text = 'N'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONINFO)
        self.assertEqual(root.signonrealm, 'AMERITRADE')
        self.assertEqual(root.min, 4)
        self.assertEqual(root.max, 32)
        self.assertEqual(root.chartype, 'ALPHAORNUMERIC')
        self.assertEqual(root.casesen, True)
        self.assertEqual(root.special, False)
        self.assertEqual(root.spaces, False)
        self.assertEqual(root.pinch, False)
        self.assertEqual(root.chgpinfirst, False)
        # self.assertEqual(root.usercred1label, 'What is your name?')
        # self.assertEqual(root.usercred2label, 'What is your favorite color?')
        # self.assertEqual(root.clientuidreq, False)
        # self.assertEqual(root.authtokenfirst, True)
        # self.assertEqual(root.authtokenlabel, 'Enigma')
        # self.assertEqual(root.authtokeninfourl, 'http://www.google.com')
        # self.assertEqual(root.mfachallengesupt, False)
        # self.assertEqual(root.mfachallengefirst, True)
        # self.assertEqual(root.accesstokenreq, False)

    def testOneOf(self):
        self.oneOfTest('CHARTYPE', ('ALPHAONLY', 'NUMERICONLY',
                                    'ALPHAORNUMERIC', 'ALPHAANDNUMERIC'))


class SignoninfolistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNONINFOLIST')
        # for i in range(2):
        for i in range(1):
            signoninfo = SignoninfoTestCase().root
            root.append(signoninfo)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONINFOLIST)
        # self.assertEqual(len(root), 2)
        self.assertEqual(len(root), 1)
        for child in root:
            self.assertIsInstance(child, SIGNONINFO)


class Signonmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNONMSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)


class SignonmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNONMSGSET')
        signonmsgsetv1 = Signonmsgsetv1TestCase().root
        root.append(signonmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSET)
        self.assertIsInstance(root.signonmsgsetv1, SIGNONMSGSETV1)


if __name__ == '__main__':
    unittest.main()
