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
from ofxtools.models.common import (MSGSETCORE, STATUS, SVCSTATUSES)
from ofxtools.models.signup import (
    CLIENTENROLL, WEBENROLL, OTHERENROLL, SIGNUPMSGSETV1, SIGNUPMSGSET,
    ACCTINFORQ, ACCTINFORS, ACCTINFOTRNRQ, ACCTINFOTRNRS,
    SIGNUPMSGSRQV1, SIGNUPMSGSRSV1,
    BANKACCTINFO, CCACCTINFO, INVACCTINFO, ACCTINFO,
    ENROLLRQ, ENROLLRS, ENROLLTRNRQ, ENROLLTRNRS,
    SVCADD, SVCCHG, SVCDEL, ACCTRQ, ACCTRS, ACCTTRNRQ, ACCTTRNRS,
    ACCTSYNCRQ, ACCTSYNCRS,
    CHGUSERINFORQ, CHGUSERINFORS, CHGUSERINFOTRNRQ, CHGUSERINFOTRNRS,
    CHGUSERINFOSYNCRQ, CHGUSERINFOSYNCRS, SVCS
)
from ofxtools.models.bank import (BANKACCTFROM, BANKACCTTO, CCACCTFROM, CCACCTTO)
from ofxtools.models.investment import (INVACCTFROM, INVACCTTO, )
from ofxtools.utils import UTC
from ofxtools.models.i18n import COUNTRY_CODES

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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CLIENTENROLL)
        self.assertEqual(instance.acctrequired, True)


class WebenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['URL', ]

    @property
    def root(self):
        root = Element('WEBENROLL')
        SubElement(root, 'URL').text = 'http://www.ameritrade.com'
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WEBENROLL)
        self.assertEqual(instance.url, 'http://www.ameritrade.com')


class OtherenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['MESSAGE', ]

    @property
    def root(self):
        root = Element('OTHERENROLL')
        SubElement(root, 'MESSAGE').text = 'Mail me $99.99'
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, OTHERENROLL)
        self.assertEqual(instance.message, 'Mail me $99.99')


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SIGNUPMSGSETV1)
        self.assertIsInstance(instance.msgsetcore, MSGSETCORE)
        self.assertIsInstance(instance.webenroll, WEBENROLL)
        self.assertEqual(instance.chguserinfo, False)
        self.assertEqual(instance.availaccts, True)
        self.assertEqual(instance.clientactreq, False)


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SIGNUPMSGSET)
        self.assertIsInstance(instance.signupmsgsetv1, SIGNUPMSGSETV1)


class AcctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('DESC', 'PHONE', 'BANKACCTINFO', 'CCACCTINFO',
                        'INVACCTINFO', )

    @property
    def root(self):
        root = Element('ACCTINFO')
        SubElement(root, 'DESC').text = 'All accounts'
        SubElement(root, 'PHONE').text = '8675309'
        bankacctinfo = test_models_bank.BankacctinfoTestCase().root
        root.append(bankacctinfo)
        ccacctinfo = test_models_bank.CcacctinfoTestCase().root
        root.append(ccacctinfo)
        invacctinfo = test_models_investment.InvacctinfoTestCase().root
        root.append(invacctinfo)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFO)
        self.assertEqual(instance.desc, 'All accounts')
        self.assertEqual(instance.phone, '8675309')
        self.assertEqual(len(instance), 3)
        self.assertIsInstance(instance[0], BANKACCTINFO)
        self.assertIsInstance(instance[1], CCACCTINFO)
        self.assertIsInstance(instance[2], INVACCTINFO)

    def testRepr(self):
        rep = repr(Aggregate.from_etree(self.root))
        self.assertEqual(
            rep, ("<ACCTINFO desc='All accounts' phone='8675309' len=3>"))


class AcctinfoMalformedTestCase(unittest.TestCase):
    def testMissingXxxacctinfo(self):
        root = Element('ACCTINFO')

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleBankacctinfo(self):
        root = Element('ACCTINFO')
        bankacctinfo = test_models_bank.BankacctinfoTestCase().root
        root.append(bankacctinfo)
        root.append(bankacctinfo)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleCcacctinfo(self):
        root = Element('ACCTINFO')
        ccacctinfo = test_models_bank.CcacctinfoTestCase().root
        root.append(ccacctinfo)
        root.append(ccacctinfo)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleInvacctinfo(self):
        root = Element('ACCTINFO')
        invacctinfo = test_models_investment.InvacctinfoTestCase().root
        root.append(invacctinfo)
        root.append(invacctinfo)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['DTACCTUP', ]

    @property
    def root(self):
        root = Element('ACCTINFORQ')
        SubElement(root, 'DTACCTUP').text = '20120314'
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFORQ)
        self.assertEqual(instance.dtacctup, datetime(2012, 3, 14, tzinfo=UTC))


class AcctinforsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('DTACCTUP', )
    optionalElements = ('ACCTINFO', )

    @property
    def root(self):
        root = Element('ACCTINFORS')
        SubElement(root, 'DTACCTUP').text = '20120314'
        acctinfo = AcctinfoTestCase().root
        root.append(acctinfo)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFORS)
        self.assertEqual(instance.dtacctup, datetime(2012, 3, 14, tzinfo=UTC))
        self.assertEqual(len(instance), 1)
        self.assertIsInstance(instance[0], ACCTINFO)

    def testRepr(self):
        rep = repr(Aggregate.from_etree(self.root))
        self.assertEqual(
            rep, "<ACCTINFORS dtacctup='2012-03-14 00:00:00+00:00' len=1>")


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFOTRNRQ)
        self.assertEqual(instance.trnuid, 'DEADBEEF')
        self.assertIsInstance(instance.acctinforq, ACCTINFORQ)


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFOTRNRS)
        self.assertEqual(instance.trnuid, 'DEADBEEF')
        self.assertIsInstance(instance.status, STATUS)
        self.assertIsInstance(instance.acctinfors, ACCTINFORS)


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ENROLLRQ)
        self.assertEqual(instance.firstname, 'Porky')
        self.assertEqual(instance.middlename, 'D.')
        self.assertEqual(instance.lastname, 'Pig')
        self.assertEqual(instance.addr1, '3717 N Clark St')
        self.assertEqual(instance.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(instance.addr3, 'Seat A1')
        self.assertEqual(instance.city, 'Chicago')
        self.assertEqual(instance.state, 'IL')
        self.assertEqual(instance.postalcode, '60613')
        self.assertEqual(instance.country, 'USA')
        self.assertEqual(instance.dayphone, '(773) 309-1027')
        self.assertEqual(instance.evephone, '867-5309')
        self.assertEqual(instance.userid, 'bacon2b')
        self.assertEqual(instance.taxid, '123456789')
        self.assertEqual(instance.securityname, 'Petunia')
        self.assertEqual(instance.datebirth, datetime(2016, 7, 5, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest('COUNTRY', COUNTRY_CODES)


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ENROLLRS)
        self.assertEqual(instance.userid, 'bacon2b')
        self.assertEqual(instance.dtexpire, datetime(2016, 7, 5, tzinfo=UTC))


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ENROLLTRNRQ)
        self.assertEqual(instance.trnuid, 'DEADBEEF')
        self.assertIsInstance(instance.enrollrq, ENROLLRQ)


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ENROLLTRNRS)
        self.assertEqual(instance.trnuid, 'DEADBEEF')
        self.assertIsInstance(instance.status, STATUS)
        self.assertIsInstance(instance.enrollrs, ENROLLRS)


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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SIGNUPMSGSRQV1)
        self.assertEqual(len(instance), 2)
        for stmttrnrs in instance:
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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SIGNUPMSGSRSV1)
        self.assertEqual(len(instance), 2)
        for stmttrnrs in instance:
            self.assertIsInstance(stmttrnrs, ENROLLTRNRS)


class SvcaddBankTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCADD')
        acctto = test_models_bank.BankaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCADD)
        self.assertIsInstance(instance.bankacctto, BANKACCTTO)


class SvcaddCcTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCADD')
        acctto = test_models_bank.CcaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCADD)
        self.assertIsInstance(instance.ccacctto, CCACCTTO)


class SvcaddInvTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCADD')
        acctto = test_models_investment.InvaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCADD)
        self.assertIsInstance(instance.invacctto, INVACCTTO)


class SvcaddMalformedTestCase(unittest.TestCase):
    def testXxxaccttoMissing(self):
        root = Element('SVCADD')
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctto(self):
        bankacctto = test_models_bank.BankaccttoTestCase().root
        ccacctto = test_models_bank.CcaccttoTestCase().root
        invacctto = test_models_investment.InvaccttoTestCase().root

        root = Element('SVCADD')
        root.append(bankacctto)
        root.append(ccacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCADD')
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCADD')
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class SvcchgBankTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCCHG')
        acctfrom = test_models_bank.BankacctfromTestCase().root
        root.append(acctfrom)
        acctto = test_models_bank.BankaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCCHG)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.bankacctto, BANKACCTTO)


class SvcchgCcTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCCHG')
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        acctto = test_models_bank.CcaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCCHG)
        self.assertIsInstance(instance.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(instance.ccacctto, CCACCTTO)


class SvcchgInvTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCCHG')
        acctfrom = test_models_investment.InvacctfromTestCase().root
        root.append(acctfrom)
        acctto = test_models_investment.InvaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCCHG)
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)
        self.assertIsInstance(instance.invacctto, INVACCTTO)


class SvcchgMalformedTestCase(unittest.TestCase):
    def testXxxaccttoMissing(self):
        root = Element('SVCCHG')
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctfrom(self):
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        ccacctfrom = test_models_bank.CcacctfromTestCase().root
        invacctfrom = test_models_investment.InvacctfromTestCase().root
        bankacctto = test_models_bank.BankaccttoTestCase().root

        root = Element('SVCADD')
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(bankacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCADD')
        root.append(bankacctfrom)
        root.append(invacctfrom)
        root.append(bankacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCADD')
        root.append(ccacctfrom)
        root.append(invacctfrom)
        root.append(bankacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctto(self):
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        bankacctto = test_models_bank.BankaccttoTestCase().root
        ccacctto = test_models_bank.CcaccttoTestCase().root
        invacctto = test_models_investment.InvaccttoTestCase().root

        root = Element('SVCADD')
        root.append(bankacctfrom)
        root.append(bankacctto)
        root.append(ccacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCADD')
        root.append(bankacctfrom)
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCADD')
        root.append(bankacctfrom)
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class SvcdelBankTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCDEL')
        acctfrom = test_models_bank.BankacctfromTestCase().root
        root.append(acctfrom)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SVCDEL)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)


class SvcdelCcTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCDEL')
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SVCDEL)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)


class SvcdelInvTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element('SVCDEL')
        acctfrom = test_models_investment.InvacctfromTestCase().root
        root.append(acctfrom)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SVCDEL)
        self.assertIsInstance(root.invacctfrom, INVACCTFROM)


class SvcdelMalformedTestCase(unittest.TestCase):
    def testXxxacctfromMissing(self):
        root = Element('SVCDEL')
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctfrom(self):
        bankacctfrom = test_models_bank.BankacctfromTestCase().root
        ccacctfrom = test_models_bank.CcacctfromTestCase().root
        invacctfrom = test_models_investment.InvacctfromTestCase().root

        root = Element('SVCDEL')
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCDEL')
        root.append(bankacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('SVCDEL')
        root.append(bankacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctrqSvcaddTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('SVC', )

    @property
    def root(self):
        root = Element('ACCTRQ')
        svcadd = SvcaddBankTestCase().root
        root.append(svcadd)
        SubElement(root, 'SVC').text = 'BANKSVC'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRQ)
        self.assertIsInstance(root.svcadd, SVCADD)
        self.assertEqual(root.svc, 'BANKSVC')

    def testOneOf(self):
        self.oneOfTest('SVC', SVCS)


class AcctrqSvcchgTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('SVC', )

    @property
    def root(self):
        root = Element('ACCTRQ')
        svcchg = SvcchgBankTestCase().root
        root.append(svcchg)
        SubElement(root, 'SVC').text = 'BANKSVC'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRQ)
        self.assertIsInstance(root.svcchg, SVCCHG)
        self.assertEqual(root.svc, 'BANKSVC')

    def testOneOf(self):
        self.oneOfTest('SVC', SVCS)


class AcctrqSvcdelTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('SVC', )

    @property
    def root(self):
        root = Element('ACCTRQ')
        svcdel = SvcdelBankTestCase().root
        root.append(svcdel)
        SubElement(root, 'SVC').text = 'BANKSVC'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRQ)
        self.assertIsInstance(root.svcdel, SVCDEL)
        self.assertEqual(root.svc, 'BANKSVC')

    def testOneOf(self):
        self.oneOfTest('SVC', SVCS)


class AcctrqMalformedTestCase(unittest.TestCase):
    def testSvcxxxMissing(self):
        root = Element('ACCTRQ')
        SubElement(root, 'SVC').text = 'BANKSVC'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedSvcxxx(self):
        svcadd = SvcaddBankTestCase().root
        svcchg = SvcchgBankTestCase().root
        svcdel = SvcdelBankTestCase().root

        root = Element('ACCTRQ')
        root.append(svcadd)
        root.append(svcchg)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('ACCTRQ')
        root.append(svcadd)
        root.append(svcdel)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('ACCTRQ')
        root.append(svcchg)
        root.append(svcdel)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('ACCTRQ')
        root.append(svcadd)
        root.append(svcchg)
        root.append(svcdel)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctrsSvcaddTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('SVC', 'SVCSTATUS')

    @property
    def root(self):
        root = Element('ACCTRS')
        svcadd = SvcaddBankTestCase().root
        root.append(svcadd)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRS)
        self.assertIsInstance(root.svcadd, SVCADD)
        self.assertEqual(root.svc, 'BANKSVC')

    def testOneOf(self):
        self.oneOfTest('SVC', SVCS)
        self.oneOfTest('SVCSTATUS', SVCSTATUSES)


class AcctrsSvcchgTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('SVC', 'SVCSTATUS')

    @property
    def root(self):
        root = Element('ACCTRS')
        svcchg = SvcchgBankTestCase().root
        root.append(svcchg)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRS)
        self.assertIsInstance(root.svcchg, SVCCHG)
        self.assertEqual(root.svc, 'BANKSVC')

    def testOneOf(self):
        self.oneOfTest('SVC', SVCS)
        self.oneOfTest('SVCSTATUS', SVCSTATUSES)


class AcctrsSvcdelTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('SVC', 'SVCSTATUS')

    @property
    def root(self):
        root = Element('ACCTRS')
        svcdel = SvcdelBankTestCase().root
        root.append(svcdel)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRS)
        self.assertIsInstance(root.svcdel, SVCDEL)
        self.assertEqual(root.svc, 'BANKSVC')

    def testOneOf(self):
        self.oneOfTest('SVC', SVCS)
        self.oneOfTest('SVCSTATUS', SVCSTATUSES)


class AcctrsMalformedTestCase(unittest.TestCase):
    def testSvcxxxMissing(self):
        root = Element('ACCTRS')
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedSvcxxx(self):
        svcadd = SvcaddBankTestCase().root
        svcchg = SvcchgBankTestCase().root
        svcdel = SvcdelBankTestCase().root

        root = Element('ACCTRS')
        root.append(svcadd)
        root.append(svcchg)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('ACCTRS')
        root.append(svcadd)
        root.append(svcdel)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('ACCTRS')
        root.append(svcchg)
        root.append(svcdel)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element('ACCTRS')
        root.append(svcadd)
        root.append(svcchg)
        root.append(svcdel)
        SubElement(root, 'SVC').text = 'BANKSVC'
        SubElement(root, 'SVCSTATUS').text = 'AVAIL'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AccttrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'ACCTRQ', )

    @property
    def root(self):
        root = Element('ACCTTRNRQ')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        acctrq = AcctrqSvcaddTestCase().root
        root.append(acctrq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTTRNRQ)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.acctrq, ACCTRQ)


class AccttrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'ACCTRS', )

    @property
    def root(self):
        root = Element('ACCTTRNRS')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        acctrs = AcctrsSvcaddTestCase().root
        root.append(acctrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTTRNRS)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.acctrs, ACCTRS)


###############################################################################


class AcctsyncrqTokenTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        accttrnrq = AccttrnrqTestCase().root
        root.append(accttrnrq)
        root.append(accttrnrq)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTSYNCRQ)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.rejectifmissing, True)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], ACCTTRNRQ)
        self.assertIsInstance(instance[1], ACCTTRNRQ)


class AcctsyncrqTokenonlyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'TOKENONLY').text = 'Y'
        SubElement(root, 'REJECTIFMISSING').text = 'N'
        accttrnrq = AccttrnrqTestCase().root
        root.append(accttrnrq)
        root.append(accttrnrq)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTSYNCRQ)
        self.assertEqual(instance.tokenonly, True)
        self.assertEqual(instance.rejectifmissing, False)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], ACCTTRNRQ)
        self.assertIsInstance(instance[1], ACCTTRNRQ)


class AcctsyncrqRefreshTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'REFRESH').text = 'Y'
        SubElement(root, 'REJECTIFMISSING').text = 'N'
        accttrnrq = AccttrnrqTestCase().root
        root.append(accttrnrq)
        root.append(accttrnrq)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTSYNCRQ)
        self.assertEqual(instance.refresh, True)
        self.assertEqual(instance.rejectifmissing, False)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], ACCTTRNRQ)
        self.assertIsInstance(instance[1], ACCTTRNRQ)


class AcctsyncrqEmptyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTSYNCRQ)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.rejectifmissing, True)
        self.assertEqual(len(instance), 0)


class AcctsyncrqMalformedTestCase(unittest.TestCase):
    def testTokenWithTokenOnly(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'TOKENONLY').text = 'N'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        accttrnrq = AccttrnrqTestCase().root
        root.append(accttrnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testTokenWithRefresh(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'REFRESH').text = 'N'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        accttrnrq = AccttrnrqTestCase().root
        root.append(accttrnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testTokenonlyWithRefresh(self):
        root = Element('ACCTSYNCRQ')
        SubElement(root, 'TOKENONLY').text = 'N'
        SubElement(root, 'REFRESH').text = 'N'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        accttrnrq = AccttrnrqTestCase().root
        root.append(accttrnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctsyncrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TOKEN', )
    optionalElements = ('LOSTSYNC', )

    @property
    def root(self):
        root = Element('ACCTSYNCRS')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'LOSTSYNC').text = 'Y'
        accttrnrs = AccttrnrsTestCase().root
        root.append(accttrnrs)
        root.append(accttrnrs)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTSYNCRS)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.lostsync, True)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], ACCTTRNRS)
        self.assertIsInstance(instance[1], ACCTTRNRS)

    def testMissingAccttrnrs(self):
        root = deepcopy(self.root)
        for accttrnrs in root.findall('ACCTTRNRS'):
            root.remove(accttrnrs)
        instance = Aggregate.from_etree(root)
        self.assertIsInstance(instance, ACCTSYNCRS)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.lostsync, True)
        self.assertEqual(len(instance), 0)


class ChguserinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ('FIRSTNAME', 'MIDDLENAME', 'LASTNAME', 'ADDR1',
                        'ADDR2', 'ADDR3', 'CITY', 'STATE', 'POSTALCODE',
                        'COUNTRY', 'DAYPHONE', 'EVEPHONE', 'EMAIL', )

    @property
    def root(self):
        root = Element('CHGUSERINFORQ')
        SubElement(root, 'FIRSTNAME').text = 'Mary'
        SubElement(root, 'MIDDLENAME').text = 'J.'
        SubElement(root, 'LASTNAME').text = 'Blige'
        SubElement(root, 'ADDR1').text = '3717 N Clark St'
        SubElement(root, 'ADDR2').text = 'Dugout Box, Aisle 19'
        SubElement(root, 'ADDR3').text = 'Seat A1'
        SubElement(root, 'CITY').text = 'Chicago'
        SubElement(root, 'STATE').text = 'IL'
        SubElement(root, 'POSTALCODE').text = '60613'
        SubElement(root, 'COUNTRY').text = 'USA'
        SubElement(root, 'DAYPHONE').text = '(773) 309-1027'
        SubElement(root, 'EVEPHONE').text = '867-5309'
        SubElement(root, 'EMAIL').text = 'test@example.com'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CHGUSERINFORQ)
        self.assertEqual(root.firstname, 'Mary')
        self.assertEqual(root.middlename, 'J.')
        self.assertEqual(root.lastname, 'Blige')
        self.assertEqual(root.addr1, '3717 N Clark St')
        self.assertEqual(root.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(root.addr3, 'Seat A1')
        self.assertEqual(root.city, 'Chicago')
        self.assertEqual(root.state, 'IL')
        self.assertEqual(root.postalcode, '60613')
        self.assertEqual(root.country, 'USA')
        self.assertEqual(root.dayphone, '(773) 309-1027')
        self.assertEqual(root.evephone, '867-5309')
        self.assertEqual(root.email, 'test@example.com')


class ChguserinforsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('DTINFOCHG', )
    optionalElements = ('FIRSTNAME', 'MIDDLENAME', 'LASTNAME', 'ADDR1',
                        'ADDR2', 'ADDR3', 'CITY', 'STATE', 'POSTALCODE',
                        'COUNTRY', 'DAYPHONE', 'EVEPHONE', 'EMAIL', )

    @property
    def root(self):
        root = Element('CHGUSERINFORS')
        SubElement(root, 'FIRSTNAME').text = 'Mary'
        SubElement(root, 'MIDDLENAME').text = 'J.'
        SubElement(root, 'LASTNAME').text = 'Blige'
        SubElement(root, 'ADDR1').text = '3717 N Clark St'
        SubElement(root, 'ADDR2').text = 'Dugout Box, Aisle 19'
        SubElement(root, 'ADDR3').text = 'Seat A1'
        SubElement(root, 'CITY').text = 'Chicago'
        SubElement(root, 'STATE').text = 'IL'
        SubElement(root, 'POSTALCODE').text = '60613'
        SubElement(root, 'COUNTRY').text = 'USA'
        SubElement(root, 'DAYPHONE').text = '(773) 309-1027'
        SubElement(root, 'EVEPHONE').text = '867-5309'
        SubElement(root, 'EMAIL').text = 'test@example.com'
        SubElement(root, 'DTINFOCHG').text = '20141122'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CHGUSERINFORS)
        self.assertEqual(root.firstname, 'Mary')
        self.assertEqual(root.middlename, 'J.')
        self.assertEqual(root.lastname, 'Blige')
        self.assertEqual(root.addr1, '3717 N Clark St')
        self.assertEqual(root.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(root.addr3, 'Seat A1')
        self.assertEqual(root.city, 'Chicago')
        self.assertEqual(root.state, 'IL')
        self.assertEqual(root.postalcode, '60613')
        self.assertEqual(root.country, 'USA')
        self.assertEqual(root.dayphone, '(773) 309-1027')
        self.assertEqual(root.evephone, '867-5309')
        self.assertEqual(root.email, 'test@example.com')
        self.assertEqual(root.dtinfochg, datetime(2014, 11, 22, tzinfo=UTC))


class ChguserinfotrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'CHGUSERINFORQ', )

    @property
    def root(self):
        root = Element('CHGUSERINFOTRNRQ')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        chguserinforq = ChguserinforqTestCase().root
        root.append(chguserinforq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CHGUSERINFOTRNRQ)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.chguserinforq, CHGUSERINFORQ)


class ChguserinfotrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', 'CHGUSERINFORS', )

    @property
    def root(self):
        root = Element('CHGUSERINFOTRNRS')
        SubElement(root, 'TRNUID').text = 'DEADBEEF'
        chguserinfors = ChguserinforsTestCase().root
        root.append(chguserinfors)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CHGUSERINFOTRNRS)
        self.assertEqual(root.trnuid, 'DEADBEEF')
        self.assertIsInstance(root.chguserinfors, CHGUSERINFORS)


class ChguserinfosyncrqTokenTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        chguserinfotrnrq = ChguserinfotrnrqTestCase().root
        root.append(chguserinfotrnrq)
        root.append(chguserinfotrnrq)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHGUSERINFOSYNCRQ)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.rejectifmissing, True)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], CHGUSERINFOTRNRQ)
        self.assertIsInstance(instance[1], CHGUSERINFOTRNRQ)


class ChguserinfosyncrqTokenonlyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'TOKENONLY').text = 'Y'
        SubElement(root, 'REJECTIFMISSING').text = 'N'
        chguserinfotrnrq = ChguserinfotrnrqTestCase().root
        root.append(chguserinfotrnrq)
        root.append(chguserinfotrnrq)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHGUSERINFOSYNCRQ)
        self.assertEqual(instance.tokenonly, True)
        self.assertEqual(instance.rejectifmissing, False)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], CHGUSERINFOTRNRQ)
        self.assertIsInstance(instance[1], CHGUSERINFOTRNRQ)


class ChguserinfosyncrqRefreshTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'REFRESH').text = 'Y'
        SubElement(root, 'REJECTIFMISSING').text = 'N'
        chguserinfotrnrq = ChguserinfotrnrqTestCase().root
        root.append(chguserinfotrnrq)
        root.append(chguserinfotrnrq)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHGUSERINFOSYNCRQ)
        self.assertEqual(instance.refresh, True)
        self.assertEqual(instance.rejectifmissing, False)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], CHGUSERINFOTRNRQ)
        self.assertIsInstance(instance[1], CHGUSERINFOTRNRQ)


class ChguserinfosyncrqEmptyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('REJECTIFMISSING', )

    @property
    def root(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHGUSERINFOSYNCRQ)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.rejectifmissing, True)
        self.assertEqual(len(instance), 0)


class ChguserinfosyncrqMalformedTestCase(unittest.TestCase):
    def testTokenWithTokenOnly(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'TOKENONLY').text = 'N'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        chguserinfotrnrq = ChguserinfotrnrqTestCase().root
        root.append(chguserinfotrnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testTokenWithRefresh(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'REFRESH').text = 'N'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        chguserinfotrnrq = ChguserinfotrnrqTestCase().root
        root.append(chguserinfotrnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testTokenonlyWithRefresh(self):
        root = Element('CHGUSERINFOSYNCRQ')
        SubElement(root, 'TOKENONLY').text = 'N'
        SubElement(root, 'REFRESH').text = 'N'
        SubElement(root, 'REJECTIFMISSING').text = 'Y'
        chguserinfotrnrq = ChguserinfotrnrqTestCase().root
        root.append(chguserinfotrnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class ChguserinfosyncrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TOKEN', )
    optionalElements = ('LOSTSYNC', )

    @property
    def root(self):
        root = Element('CHGUSERINFOSYNCRS')
        SubElement(root, 'TOKEN').text = 'DEADBEEF'
        SubElement(root, 'LOSTSYNC').text = 'Y'
        chguserinfotrnrs = ChguserinfotrnrsTestCase().root
        root.append(chguserinfotrnrs)
        root.append(chguserinfotrnrs)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHGUSERINFOSYNCRS)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.lostsync, True)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], CHGUSERINFOTRNRS)
        self.assertIsInstance(instance[1], CHGUSERINFOTRNRS)

    def testMissingAccttrnrs(self):
        root = deepcopy(self.root)
        for accttrnrs in root.findall('CHGUSERINFOTRNRS'):
            root.remove(accttrnrs)
        instance = Aggregate.from_etree(root)
        self.assertIsInstance(instance, CHGUSERINFOSYNCRS)
        self.assertEqual(instance.token, 'DEADBEEF')
        self.assertEqual(instance.lostsync, True)
        self.assertEqual(len(instance), 0)


if __name__ == '__main__':
    unittest.main()
