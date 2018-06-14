# coding: utf-8
""" """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from datetime import datetime


# local imports
from ofxtools.models.base import (
    Aggregate,
)
from ofxtools.models.common import (STATUS, MSGSETCORE, )
from ofxtools.models.profile import (
    PROFRQ, PROFRS, PROFTRNRQ, PROFTRNRS, MSGSETLIST, PROFMSGSETV1, PROFMSGSET,
)
from ofxtools.models.signon import (SIGNONINFOLIST, )
from ofxtools.utils import UTC

from . import base
from . import test_models_common
from . import test_signon
from . import test_signup
from . import test_bank
from . import test_creditcard
from . import test_investment
from . import test_seclist
from . import test_tax1099


class ProfrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['CLIENTROUTING', 'DTPROFUP', ]

    @property
    def root(self):
        root = Element('PROFRQ')
        SubElement(root, 'CLIENTROUTING').text = 'SERVICE'
        SubElement(root, 'DTPROFUP').text = '20010401'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFRQ)
        self.assertEqual(root.clientrouting, 'SERVICE')
        self.assertEqual(root.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest('CLIENTROUTING', ('NONE', 'SERVICE', 'MSGSET'))


class ProftrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('PROFTRNRQ')
        SubElement(root, 'TRNUID').text = 'efe1790a-2f45-47fa-b439-9ae7682dc2a4'
        profrq = ProfrqTestCase().root
        root.append(profrq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFTRNRQ)
        self.assertEqual(root.trnuid, 'efe1790a-2f45-47fa-b439-9ae7682dc2a4')
        self.assertIsInstance(root.profrq, PROFRQ)


class MsgsetlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('MSGSETLIST')
        signon = test_signon.SignonmsgsetTestCase().root
        root.append(signon)
        signup = test_signup.SignupmsgsetTestCase().root
        root.append(signup)
        bankmsgset = test_bank.BankmsgsetTestCase().root
        root.append(bankmsgset)
        creditcardmsgset = test_creditcard.CreditcardmsgsetTestCase().root
        root.append(creditcardmsgset)
        invstmtmsgset = test_investment.InvstmtmsgsetTestCase().root
        root.append(invstmtmsgset)
        seclistmsgset = test_seclist.SeclistmsgsetTestCase().root
        root.append(seclistmsgset)
        profmsgset = ProfmsgsetTestCase().root
        root.append(profmsgset)
        tax1099msgset = test_tax1099.Tax1099msgsetTestCase().root
        root.append(tax1099msgset)
        return root


class ProfrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['MSGSETLIST', 'SIGNONINFOLIST', 'DTPROFUP', 'FINAME',
                        'ADDR1', 'CITY', 'STATE', 'POSTALCODE', 'COUNTRY', ]
    optionalElements = ['ADDR2', 'ADDR3', 'CSPHONE', 'TSPHONE', 'FAXPHONE',
                        'URL', 'EMAIL', ]

    @property
    def root(self):
        root = Element('PROFRS')
        msgsetlist = MsgsetlistTestCase().root
        root.append(msgsetlist)
        signoninfolist = test_signon.SignoninfolistTestCase().root
        root.append(signoninfolist)
        SubElement(root, 'DTPROFUP').text = '20010401'
        SubElement(root, 'FINAME').text = 'Dewey Cheatham & Howe'
        SubElement(root, 'ADDR1').text = '3717 N Clark St'
        SubElement(root, 'ADDR2').text = 'Dugout Box, Aisle 19'
        SubElement(root, 'ADDR3').text = 'Seat A1'
        SubElement(root, 'CITY').text = 'Chicago'
        SubElement(root, 'STATE').text = 'IL'
        SubElement(root, 'POSTALCODE').text = '60613'
        SubElement(root, 'COUNTRY').text = 'USA'
        SubElement(root, 'CSPHONE').text = '(773) 309-1027'
        SubElement(root, 'TSPHONE').text = '(773) 309-1028'
        SubElement(root, 'FAXPHONE').text = '(773) 309-1029'
        SubElement(root, 'URL').text = 'http://www.ameritrade.com'
        SubElement(root, 'EMAIL').text = 'support@ameritrade.com'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFRS)
        self.assertIsInstance(root.msgsetlist, MSGSETLIST)
        self.assertIsInstance(root.signoninfolist, SIGNONINFOLIST)
        self.assertEqual(root.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))
        self.assertEqual(root.finame, 'Dewey Cheatham & Howe')
        self.assertEqual(root.addr1, '3717 N Clark St')
        self.assertEqual(root.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(root.addr3, 'Seat A1')
        self.assertEqual(root.city, 'Chicago')
        self.assertEqual(root.state, 'IL')
        self.assertEqual(root.postalcode, '60613')
        self.assertEqual(root.country, 'USA')
        self.assertEqual(root.csphone, '(773) 309-1027')
        self.assertEqual(root.tsphone, '(773) 309-1028')
        self.assertEqual(root.faxphone, '(773) 309-1029')
        self.assertEqual(root.url, 'http://www.ameritrade.com')
        self.assertEqual(root.email, 'support@ameritrade.com')


class ProftrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('PROFTRNRS')
        SubElement(root, 'TRNUID').text = 'efe1790a-2f45-47fa-b439-9ae7682dc2a4'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        profrs = ProfrsTestCase().root
        root.append(profrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFTRNRS)
        self.assertEqual(root.trnuid, 'efe1790a-2f45-47fa-b439-9ae7682dc2a4')
        self.assertIsInstance(root.status, STATUS)
        self.assertIsInstance(root.profrs, PROFRS)


class Profmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['MSGSETCORE', ]

    @property
    def root(self):
        root = Element('PROFMSGSETV1')
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
        root = Element('PROFMSGSET')
        msgsetv1 = Profmsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSET)
        self.assertIsInstance(root.profmsgsetv1, PROFMSGSETV1)


if __name__ == '__main__':
    unittest.main()
