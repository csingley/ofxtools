# coding: utf-8
""" Unit tests for ofxtools.models.signup """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import (
    Aggregate,
)
from ofxtools.models.common import (MSGSETCORE, STATUS)
from ofxtools.models.signup import (
    CLIENTENROLL, WEBENROLL, OTHERENROLL, SIGNUPMSGSETV1, SIGNUPMSGSET,
    ACCTINFORQ, ACCTINFORS, ACCTINFOTRNRQ, ACCTINFOTRNRS,
    SIGNUPMSGSRQV1, SIGNUPMSGSRSV1,
    BANKACCTINFO, CCACCTINFO, INVACCTINFO, ACCTINFO,
    ENROLLRQ, ENROLLRS, ENROLLTRNRQ, ENROLLTRNRS,
)
from ofxtools.models.bank import BANKACCTFROM
from ofxtools.models.creditcard import CCACCTFROM
from ofxtools.models.investment import INVACCTFROM
from ofxtools.utils import UTC

import base
import test_models_common
import test_models_bank
import test_models_investment


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


class BankacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('BANKACCTFROM', 'SVCSTATUS', )
    unsupported = ('SUPTXDL', 'XFERSRC', 'XFERDEST', )

    @property
    def root(self):
        root = Element('BANKACCTINFO')
        acctfrom = test_models_bank.BankacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKACCTINFO)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertEqual(root.svcstatus, 'AVAIL')


class CcacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('CCACCTFROM', 'SVCSTATUS', )

    @property
    def root(self):
        root = Element('CCACCTINFO')
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, 'SVCSTATUS').text = 'PEND'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCACCTINFO)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertEqual(root.svcstatus, 'PEND')


class InvacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('INVACCTFROM', 'SVCSTATUS', )

    @property
    def root(self):
        root = Element('INVACCTINFO')
        acctfrom = test_models_investment.InvacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, 'SVCSTATUS').text = 'ACTIVE'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVACCTINFO)
        self.assertIsInstance(root.invacctfrom, INVACCTFROM)
        self.assertEqual(root.svcstatus, 'ACTIVE')


class AcctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('DESC', 'PHONE', 'BANKACCTINFO', 'CCACCTINFO',
                        'INVACCTINFO', )

    @property
    def root(self):
        root = Element('ACCTINFO')
        SubElement(root, 'DESC').text = 'All accounts'
        SubElement(root, 'PHONE').text = '8675309'
        bankacctinfo = BankacctinfoTestCase().root
        root.append(bankacctinfo)
        ccacctinfo = CcacctinfoTestCase().root
        root.append(ccacctinfo)
        invacctinfo = InvacctinfoTestCase().root
        root.append(invacctinfo)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTINFO)
        self.assertEqual(root.desc, 'All accounts')
        self.assertEqual(root.phone, '8675309')
        self.assertIsInstance(root.bankacctinfo, BANKACCTINFO)
        self.assertIsInstance(root.ccacctinfo, CCACCTINFO)
        self.assertIsInstance(root.invacctinfo, INVACCTINFO)


class AcctinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['DTACCTUP', ]

    @property
    def root(self):
        root = Element('ACCTINFORQ')
        SubElement(root, 'DTACCTUP').text = '20120314'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTINFORQ)
        self.assertEqual(root.dtacctup, datetime(2012, 3, 14, tzinfo=UTC))


class AcctinforsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['DTACCTUP', ]
    optionalElements = ['ACCTINFO', ]

    @property
    def root(self):
        root = Element('ACCTINFORS')
        SubElement(root, 'DTACCTUP').text = '20120314'
        acctinfo = AcctinfoTestCase().root
        root.append(acctinfo)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTINFORS)
        self.assertEqual(root.dtacctup, datetime(2012, 3, 14, tzinfo=UTC))
        self.assertEqual(len(root), 1)
        self.assertIsInstance(root[0], ACCTINFO)


class AcctinfotrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'ACCTINFORQ', )

    @property
    def root(self):
        root = Element('ACCTINFOTRNRQ')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        acctinforq = AcctinforqTestCase().root
        root.append(acctinforq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTINFOTRNRQ)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.acctinforq, ACCTINFORQ)


class AcctinfotrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'STATUS', )
    optionalElements = ('ACCTINFORS', )

    @property
    def root(self):
        root = Element('ACCTINFOTRNRS')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        acctinfors = AcctinforsTestCase().root
        root.append(acctinfors)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTINFOTRNRS)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.status, STATUS)
        self.assertIsInstance(root.acctinfors, ACCTINFORS)


#  ENROLLRQ, ENROLLTRNRQ, ENROLLRS, ENROLLTRNRS,


class EnrollrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('FIRSTNAME', 'LASTNAME', 'ADDR1', 'CITY', 'STATE',
                        'POSTALCODE', 'EMAIL', )
    # FIXME BANKACCTFROM/CCACCTFROM/INVACCTFROM mutex
    optionalElements = ('MIDDLENAME', 'ADDR2', 'ADDR3', 'COUNTRY', 'DAYPHONE',
                        'EVEPHONE', 'USERID', 'TAXID', 'SECURITYNAME',
                        'DATEBIRTH', )

    @property
    def root(self):
        root = Element('ENROLLRQ')
        SubElement(root, 'FIRSTNAME').text = 'Porky'
        SubElement(root, 'MIDDLENAME').text = 'D.'
        SubElement(root, 'LASTNAME').text = 'Pig'
        SubElement(root, 'ADDR1').text = '3717 N Clark St'
        SubElement(root, 'ADDR2').text = 'Dugout Box, Aisle 19'
        SubElement(root, 'ADDR3').text = 'Seat A1'
        SubElement(root, 'CITY').text = 'Chicago'
        SubElement(root, 'STATE').text = 'IL'
        SubElement(root, 'POSTALCODE').text = '60613'
        SubElement(root, 'COUNTRY').text = 'USA'
        SubElement(root, 'DAYPHONE').text = '(773) 309-1027'
        SubElement(root, 'EVEPHONE').text = '867-5309'
        SubElement(root, 'EMAIL').text = 'spam@null.void'
        SubElement(root, 'USERID').text = 'bacon2b'
        SubElement(root, 'TAXID').text = '123456789'
        SubElement(root, 'SECURITYNAME').text = 'Petunia'
        SubElement(root, 'DATEBIRTH').text = '20160705'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ENROLLRQ)
        self.assertEqual(root.firstname, 'Porky')
        self.assertEqual(root.middlename, 'D.')
        self.assertEqual(root.lastname, 'Pig')
        self.assertEqual(root.addr1, '3717 N Clark St')
        self.assertEqual(root.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(root.addr3, 'Seat A1')
        self.assertEqual(root.city, 'Chicago')
        self.assertEqual(root.state, 'IL')
        self.assertEqual(root.postalcode, '60613')
        self.assertEqual(root.country, 'USA')
        self.assertEqual(root.dayphone, '(773) 309-1027')
        self.assertEqual(root.evephone, '867-5309')
        self.assertEqual(root.userid, 'bacon2b')
        self.assertEqual(root.taxid, '123456789')
        self.assertEqual(root.securityname, 'Petunia')
        self.assertEqual(root.datebirth, datetime(2016, 7, 5, tzinfo=UTC))


class EnrollrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('TEMPPASS', 'USERID', 'DTEXPIRE', )

    @property
    def root(self):
        root = Element('ENROLLRS')
        SubElement(root, 'TEMPPASS').text = 't0ps3kr1t'
        SubElement(root, 'USERID').text = 'bacon2b'
        SubElement(root, 'DTEXPIRE').text = '20160705'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ENROLLRS)
        self.assertEqual(root.userid, 'bacon2b')
        self.assertEqual(root.dtexpire, datetime(2016, 7, 5, tzinfo=UTC))


class EnrolltrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'ENROLLRQ', )

    @property
    def root(self):
        root = Element('ENROLLTRNRQ')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        root.append(EnrollrqTestCase().root)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ENROLLTRNRQ)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.enrollrq, ENROLLRQ)


class EnrolltrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'STATUS', 'ENROLLRS', )

    @property
    def root(self):
        root = Element('ENROLLTRNRS')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        root.append(EnrollrsTestCase().root)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ENROLLTRNRS)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.status, STATUS)
        self.assertIsInstance(root.enrollrs, ENROLLRS)


class Signupmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNUPMSGSRQV1')
        for i in range(2):
            enrolltrnrq = EnrolltrnrqTestCase().root
            root.append(enrolltrnrq)
        return root

    def testMemberTags(self):
        # SIGNUPMSGSRQV1 may only contain ENROLLTRNRQ
        allowedTags = SIGNUPMSGSRQV1.memberTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(EnrolltrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNUPMSGSRQV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, ENROLLTRNRQ)


class Signupmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNUPMSGSRSV1')
        for i in range(2):
            enrolltrnrs = EnrolltrnrsTestCase().root
            root.append(enrolltrnrs)
        return root

    def testMemberTags(self):
        # SIGNUPMSGSRSV1 may only contain ENROLLTRNRS
        allowedTags = SIGNUPMSGSRSV1.memberTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(EnrolltrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNUPMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, ENROLLTRNRS)


if __name__ == '__main__':
    unittest.main()
