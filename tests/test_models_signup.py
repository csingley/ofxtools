# coding: utf-8
""" Unit tests for ofxtools.models.signup """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.signup import (
    ACCTINFO,
    ACCTINFORQ,
    ACCTINFORS,
    ENROLLRQ,
    ENROLLRS,
    ENROLLTRNRQ,
    ENROLLTRNRS,
    SVCADD,
    SVCCHG,
    SVCDEL,
    SVCS,
    ACCTRQ,
    ACCTRS,
    CHGUSERINFORQ,
    CHGUSERINFORS,
    CLIENTENROLL,
    WEBENROLL,
    OTHERENROLL,
    SIGNUPMSGSRQV1,
    SIGNUPMSGSRSV1,
)
from ofxtools.models.bank import (
    BANKACCTFROM,
    BANKACCTTO,
    BANKACCTINFO,
    CCACCTFROM,
    CCACCTTO,
    CCACCTINFO,
)
from ofxtools.models.invest import INVACCTFROM, INVACCTTO, INVACCTINFO
from ofxtools.utils import UTC
from ofxtools.models.i18n import COUNTRY_CODES


# test imports
import base
from test_models_bank_stmt import (
    BankacctfromTestCase,
    BankaccttoTestCase,
    BankacctinfoTestCase,
    CcacctfromTestCase,
    CcaccttoTestCase,
    CcacctinfoTestCase,
)
from test_models_invest import (
    InvacctfromTestCase,
    InvaccttoTestCase,
    InvacctinfoTestCase,
)


class ClientenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ACCTREQUIRED"]

    @property
    def root(self):
        root = Element("CLIENTENROLL")
        SubElement(root, "ACCTREQUIRED").text = "Y"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CLIENTENROLL)
        self.assertEqual(instance.acctrequired, True)


class WebenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["URL"]

    @property
    def root(self):
        root = Element("WEBENROLL")
        SubElement(root, "URL").text = "http://www.ameritrade.com"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WEBENROLL)
        self.assertEqual(instance.url, "http://www.ameritrade.com")


class OtherenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MESSAGE"]

    @property
    def root(self):
        root = Element("OTHERENROLL")
        SubElement(root, "MESSAGE").text = "Mail me $99.99"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, OTHERENROLL)
        self.assertEqual(instance.message, "Mail me $99.99")


class AcctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ("DESC", "PHONE", "BANKACCTINFO", "CCACCTINFO", "INVACCTINFO")

    @property
    def root(self):
        root = Element("ACCTINFO")
        SubElement(root, "DESC").text = "All accounts"
        SubElement(root, "PHONE").text = "8675309"
        bankacctinfo = BankacctinfoTestCase().root
        root.append(bankacctinfo)
        ccacctinfo = CcacctinfoTestCase().root
        root.append(ccacctinfo)
        invacctinfo = InvacctinfoTestCase().root
        root.append(invacctinfo)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFO)
        self.assertEqual(instance.desc, "All accounts")
        self.assertEqual(instance.phone, "8675309")
        self.assertEqual(len(instance), 3)
        self.assertIsInstance(instance[0], BANKACCTINFO)
        self.assertIsInstance(instance[1], CCACCTINFO)
        self.assertIsInstance(instance[2], INVACCTINFO)

    def testRepr(self):
        rep = repr(Aggregate.from_etree(self.root))
        self.assertEqual(rep, ("<ACCTINFO desc='All accounts' phone='8675309' len=3>"))


class AcctinfoMalformedTestCase(unittest.TestCase):
    def testMissingXxxacctinfo(self):
        root = Element("ACCTINFO")

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleBankacctinfo(self):
        root = Element("ACCTINFO")
        bankacctinfo = BankacctinfoTestCase().root
        root.append(bankacctinfo)
        root.append(bankacctinfo)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleCcacctinfo(self):
        root = Element("ACCTINFO")
        ccacctinfo = CcacctinfoTestCase().root
        root.append(ccacctinfo)
        root.append(ccacctinfo)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleInvacctinfo(self):
        root = Element("ACCTINFO")
        invacctinfo = InvacctinfoTestCase().root
        root.append(invacctinfo)
        root.append(invacctinfo)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTACCTUP"]

    @property
    def root(self):
        root = Element("ACCTINFORQ")
        SubElement(root, "DTACCTUP").text = "20120314"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ACCTINFORQ)
        self.assertEqual(instance.dtacctup, datetime(2012, 3, 14, tzinfo=UTC))


class AcctinforsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTACCTUP"]
    optionalElements = ["ACCTINFO"]

    @property
    def root(self):
        root = Element("ACCTINFORS")
        SubElement(root, "DTACCTUP").text = "20120314"
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
        self.assertEqual(rep, "<ACCTINFORS dtacctup='2012-03-14 00:00:00+00:00' len=1>")


class AcctinfotrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = AcctinforqTestCase


class AcctinfotrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = AcctinforsTestCase


class EnrollrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "FIRSTNAME",
        "LASTNAME",
        "ADDR1",
        "CITY",
        "STATE",
        "POSTALCODE",
        "EMAIL",
    ]
    # FIXME BANKACCTFROM/CCACCTFROM/INVACCTFROM mutex
    optionalElements = [
        "MIDDLENAME",
        "ADDR2",
        "ADDR3",
        "COUNTRY",
        "DAYPHONE",
        "EVEPHONE",
        "USERID",
        "TAXID",
        "SECURITYNAME",
        "DATEBIRTH",
    ]

    @property
    def root(self):
        root = Element("ENROLLRQ")
        SubElement(root, "FIRSTNAME").text = "Porky"
        SubElement(root, "MIDDLENAME").text = "D."
        SubElement(root, "LASTNAME").text = "Pig"
        SubElement(root, "ADDR1").text = "3717 N Clark St"
        SubElement(root, "ADDR2").text = "Dugout Box, Aisle 19"
        SubElement(root, "ADDR3").text = "Seat A1"
        SubElement(root, "CITY").text = "Chicago"
        SubElement(root, "STATE").text = "IL"
        SubElement(root, "POSTALCODE").text = "60613"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "DAYPHONE").text = "(773) 309-1027"
        SubElement(root, "EVEPHONE").text = "867-5309"
        SubElement(root, "EMAIL").text = "spam@null.void"
        SubElement(root, "USERID").text = "bacon2b"
        SubElement(root, "TAXID").text = "123456789"
        SubElement(root, "SECURITYNAME").text = "Petunia"
        SubElement(root, "DATEBIRTH").text = "20160705"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ENROLLRQ)
        self.assertEqual(instance.firstname, "Porky")
        self.assertEqual(instance.middlename, "D.")
        self.assertEqual(instance.lastname, "Pig")
        self.assertEqual(instance.addr1, "3717 N Clark St")
        self.assertEqual(instance.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(instance.addr3, "Seat A1")
        self.assertEqual(instance.city, "Chicago")
        self.assertEqual(instance.state, "IL")
        self.assertEqual(instance.postalcode, "60613")
        self.assertEqual(instance.country, "USA")
        self.assertEqual(instance.dayphone, "(773) 309-1027")
        self.assertEqual(instance.evephone, "867-5309")
        self.assertEqual(instance.userid, "bacon2b")
        self.assertEqual(instance.taxid, "123456789")
        self.assertEqual(instance.securityname, "Petunia")
        self.assertEqual(instance.datebirth, datetime(2016, 7, 5, tzinfo=UTC))

        return instance

    def testOneOf(self):
        self.oneOfTest("COUNTRY", COUNTRY_CODES)


class EnrollrqBankacctfromTestCase(EnrollrqTestCase):
    @property
    def root(self):
        r = super().root
        acctfrom = BankacctfromTestCase().root
        r.append(acctfrom)
        return r

    def testConvert(self):
        instance = super().testConvert()
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)


class EnrollrqCcacctfromTestCase(EnrollrqTestCase):
    @property
    def root(self):
        r = super().root
        acctfrom = CcacctfromTestCase().root
        r.append(acctfrom)
        return r

    def testConvert(self):
        instance = super().testConvert()
        self.assertIsInstance(instance.ccacctfrom, CCACCTFROM)


class EnrollrqInvacctfromTestCase(EnrollrqTestCase):
    @property
    def root(self):
        r = super().root
        acctfrom = InvacctfromTestCase().root
        r.append(acctfrom)
        return r

    def testConvert(self):
        instance = super().testConvert()
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)


class EnrollrqMalformedTestCase(EnrollrqTestCase):
    def testMultipleAcctfrom(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        invacctfrom = InvacctfromTestCase().root

        root = super().root
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = super().root
        root.append(bankacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = super().root
        root.append(ccacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = super().root
        root.append(bankacctfrom)
        root.append(bankacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = super().root
        root.append(ccacctfrom)
        root.append(ccacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = super().root
        root.append(invacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class EnrollrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ("TEMPPASS", "USERID", "DTEXPIRE")

    @property
    def root(self):
        root = Element("ENROLLRS")
        SubElement(root, "TEMPPASS").text = "t0ps3kr1t"
        SubElement(root, "USERID").text = "bacon2b"
        SubElement(root, "DTEXPIRE").text = "20160705"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, ENROLLRS)
        self.assertEqual(instance.userid, "bacon2b")
        self.assertEqual(instance.dtexpire, datetime(2016, 7, 5, tzinfo=UTC))


class EnrolltrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = EnrollrqTestCase


class EnrolltrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = EnrollrsTestCase


class SvcaddBankTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCADD")
        acctto = BankaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCADD)
        self.assertIsInstance(instance.bankacctto, BANKACCTTO)


class SvcaddCcTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCADD")
        acctto = CcaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCADD)
        self.assertIsInstance(instance.ccacctto, CCACCTTO)


class SvcaddInvTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCADD")
        acctto = InvaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCADD)
        self.assertIsInstance(instance.invacctto, INVACCTTO)


class SvcaddMalformedTestCase(unittest.TestCase):
    def testXxxaccttoMissing(self):
        root = Element("SVCADD")
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctto(self):
        bankacctto = BankaccttoTestCase().root
        ccacctto = CcaccttoTestCase().root
        invacctto = InvaccttoTestCase().root

        root = Element("SVCADD")
        root.append(bankacctto)
        root.append(ccacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCADD")
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCADD")
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class SvcchgBankTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCCHG")
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        acctto = BankaccttoTestCase().root
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
        root = Element("SVCCHG")
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        acctto = CcaccttoTestCase().root
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
        root = Element("SVCCHG")
        acctfrom = InvacctfromTestCase().root
        root.append(acctfrom)
        acctto = InvaccttoTestCase().root
        root.append(acctto)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SVCCHG)
        self.assertIsInstance(instance.invacctfrom, INVACCTFROM)
        self.assertIsInstance(instance.invacctto, INVACCTTO)


class SvcchgMalformedTestCase(unittest.TestCase):
    def testXxxaccttoMissing(self):
        root = Element("SVCCHG")
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctfrom(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        invacctfrom = InvacctfromTestCase().root
        bankacctto = BankaccttoTestCase().root

        root = Element("SVCADD")
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(bankacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCADD")
        root.append(bankacctfrom)
        root.append(invacctfrom)
        root.append(bankacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCADD")
        root.append(ccacctfrom)
        root.append(invacctfrom)
        root.append(bankacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctto(self):
        bankacctfrom = BankacctfromTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctto = CcaccttoTestCase().root
        invacctto = InvaccttoTestCase().root

        root = Element("SVCADD")
        root.append(bankacctfrom)
        root.append(bankacctto)
        root.append(ccacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCADD")
        root.append(bankacctfrom)
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCADD")
        root.append(bankacctfrom)
        root.append(bankacctto)
        root.append(invacctto)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class SvcdelBankTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCDEL")
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SVCDEL)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)


class SvcdelCcTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCDEL")
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SVCDEL)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)


class SvcdelInvTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("SVCDEL")
        acctfrom = InvacctfromTestCase().root
        root.append(acctfrom)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SVCDEL)
        self.assertIsInstance(root.invacctfrom, INVACCTFROM)


class SvcdelMalformedTestCase(unittest.TestCase):
    def testXxxacctfromMissing(self):
        root = Element("SVCDEL")
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedXxxacctfrom(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        invacctfrom = InvacctfromTestCase().root

        root = Element("SVCDEL")
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCDEL")
        root.append(bankacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("SVCDEL")
        root.append(bankacctfrom)
        root.append(invacctfrom)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctrqTestCase(unittest.TestCase, base.TestAggregate):
    """ ACCRQ with SVCADD """

    __test__ = True

    requiredElements = ["SVC"]

    @property
    def root(self):
        root = Element("ACCTRQ")
        svcadd = SvcaddBankTestCase().root
        root.append(svcadd)
        SubElement(root, "SVC").text = "BANKSVC"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRQ)
        self.assertIsInstance(root.svcadd, SVCADD)
        self.assertEqual(root.svc, "BANKSVC")

    def testOneOf(self):
        self.oneOfTest("SVC", SVCS)


class AcctrqSvcchgTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SVC"]

    @property
    def root(self):
        root = Element("ACCTRQ")
        svcchg = SvcchgBankTestCase().root
        root.append(svcchg)
        SubElement(root, "SVC").text = "BANKSVC"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRQ)
        self.assertIsInstance(root.svcchg, SVCCHG)
        self.assertEqual(root.svc, "BANKSVC")

    def testOneOf(self):
        self.oneOfTest("SVC", SVCS)


class AcctrqSvcdelTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SVC"]

    @property
    def root(self):
        root = Element("ACCTRQ")
        svcdel = SvcdelBankTestCase().root
        root.append(svcdel)
        SubElement(root, "SVC").text = "BANKSVC"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRQ)
        self.assertIsInstance(root.svcdel, SVCDEL)
        self.assertEqual(root.svc, "BANKSVC")

    def testOneOf(self):
        self.oneOfTest("SVC", SVCS)


class AcctrqMalformedTestCase(unittest.TestCase):
    def testSvcxxxMissing(self):
        root = Element("ACCTRQ")
        SubElement(root, "SVC").text = "BANKSVC"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedSvcxxx(self):
        svcadd = SvcaddBankTestCase().root
        svcchg = SvcchgBankTestCase().root
        svcdel = SvcdelBankTestCase().root

        root = Element("ACCTRQ")
        root.append(svcadd)
        root.append(svcchg)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("ACCTRQ")
        root.append(svcadd)
        root.append(svcdel)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("ACCTRQ")
        root.append(svcchg)
        root.append(svcdel)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("ACCTRQ")
        root.append(svcadd)
        root.append(svcchg)
        root.append(svcdel)
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctrsTestCase(unittest.TestCase, base.TestAggregate):
    """ ACCRS with SVCADD """

    __test__ = True

    requiredElements = ["SVC", "SVCSTATUS"]

    @property
    def root(self):
        root = Element("ACCTRS")
        svcadd = SvcaddBankTestCase().root
        root.append(svcadd)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRS)
        self.assertIsInstance(root.svcadd, SVCADD)
        self.assertEqual(root.svc, "BANKSVC")

    def testOneOf(self):
        self.oneOfTest("SVC", SVCS)
        self.oneOfTest("SVCSTATUS", SVCSTATUSES)


class AcctrsSvcchgTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SVC", "SVCSTATUS"]

    @property
    def root(self):
        root = Element("ACCTRS")
        svcchg = SvcchgBankTestCase().root
        root.append(svcchg)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRS)
        self.assertIsInstance(root.svcchg, SVCCHG)
        self.assertEqual(root.svc, "BANKSVC")

    def testOneOf(self):
        self.oneOfTest("SVC", SVCS)
        self.oneOfTest("SVCSTATUS", SVCSTATUSES)


class AcctrsSvcdelTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SVC", "SVCSTATUS"]

    @property
    def root(self):
        root = Element("ACCTRS")
        svcdel = SvcdelBankTestCase().root
        root.append(svcdel)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ACCTRS)
        self.assertIsInstance(root.svcdel, SVCDEL)
        self.assertEqual(root.svc, "BANKSVC")

    def testOneOf(self):
        self.oneOfTest("SVC", SVCS)
        self.oneOfTest("SVCSTATUS", SVCSTATUSES)


class AcctrsMalformedTestCase(unittest.TestCase):
    def testSvcxxxMissing(self):
        root = Element("ACCTRS")
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMixedSvcxxx(self):
        svcadd = SvcaddBankTestCase().root
        svcchg = SvcchgBankTestCase().root
        svcdel = SvcdelBankTestCase().root

        root = Element("ACCTRS")
        root.append(svcadd)
        root.append(svcchg)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("ACCTRS")
        root.append(svcadd)
        root.append(svcdel)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("ACCTRS")
        root.append(svcchg)
        root.append(svcdel)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = Element("ACCTRS")
        root.append(svcadd)
        root.append(svcchg)
        root.append(svcdel)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AccttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = AcctrqTestCase


class AccttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = AcctrsTestCase


class AcctsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        trnrq = AccttrnrqTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrq))
                yield root


class AcctsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        trnrs = AccttrnrsTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root


class ChguserinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = (
        "FIRSTNAME",
        "MIDDLENAME",
        "LASTNAME",
        "ADDR1",
        "ADDR2",
        "ADDR3",
        "CITY",
        "STATE",
        "POSTALCODE",
        "COUNTRY",
        "DAYPHONE",
        "EVEPHONE",
        "EMAIL",
    )

    @property
    def root(self):
        root = Element("CHGUSERINFORQ")
        SubElement(root, "FIRSTNAME").text = "Mary"
        SubElement(root, "MIDDLENAME").text = "J."
        SubElement(root, "LASTNAME").text = "Blige"
        SubElement(root, "ADDR1").text = "3717 N Clark St"
        SubElement(root, "ADDR2").text = "Dugout Box, Aisle 19"
        SubElement(root, "ADDR3").text = "Seat A1"
        SubElement(root, "CITY").text = "Chicago"
        SubElement(root, "STATE").text = "IL"
        SubElement(root, "POSTALCODE").text = "60613"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "DAYPHONE").text = "(773) 309-1027"
        SubElement(root, "EVEPHONE").text = "867-5309"
        SubElement(root, "EMAIL").text = "test@example.com"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CHGUSERINFORQ)
        self.assertEqual(root.firstname, "Mary")
        self.assertEqual(root.middlename, "J.")
        self.assertEqual(root.lastname, "Blige")
        self.assertEqual(root.addr1, "3717 N Clark St")
        self.assertEqual(root.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(root.addr3, "Seat A1")
        self.assertEqual(root.city, "Chicago")
        self.assertEqual(root.state, "IL")
        self.assertEqual(root.postalcode, "60613")
        self.assertEqual(root.country, "USA")
        self.assertEqual(root.dayphone, "(773) 309-1027")
        self.assertEqual(root.evephone, "867-5309")
        self.assertEqual(root.email, "test@example.com")


class ChguserinforsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTINFOCHG"]
    optionalElements = [
        "FIRSTNAME",
        "MIDDLENAME",
        "LASTNAME",
        "ADDR1",
        "ADDR2",
        "ADDR3",
        "CITY",
        "STATE",
        "POSTALCODE",
        "COUNTRY",
        "DAYPHONE",
        "EVEPHONE",
        "EMAIL",
    ]

    @property
    def root(self):
        root = Element("CHGUSERINFORS")
        SubElement(root, "FIRSTNAME").text = "Mary"
        SubElement(root, "MIDDLENAME").text = "J."
        SubElement(root, "LASTNAME").text = "Blige"
        SubElement(root, "ADDR1").text = "3717 N Clark St"
        SubElement(root, "ADDR2").text = "Dugout Box, Aisle 19"
        SubElement(root, "ADDR3").text = "Seat A1"
        SubElement(root, "CITY").text = "Chicago"
        SubElement(root, "STATE").text = "IL"
        SubElement(root, "POSTALCODE").text = "60613"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "DAYPHONE").text = "(773) 309-1027"
        SubElement(root, "EVEPHONE").text = "867-5309"
        SubElement(root, "EMAIL").text = "test@example.com"
        SubElement(root, "DTINFOCHG").text = "20141122"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CHGUSERINFORS)
        self.assertEqual(root.firstname, "Mary")
        self.assertEqual(root.middlename, "J.")
        self.assertEqual(root.lastname, "Blige")
        self.assertEqual(root.addr1, "3717 N Clark St")
        self.assertEqual(root.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(root.addr3, "Seat A1")
        self.assertEqual(root.city, "Chicago")
        self.assertEqual(root.state, "IL")
        self.assertEqual(root.postalcode, "60613")
        self.assertEqual(root.country, "USA")
        self.assertEqual(root.dayphone, "(773) 309-1027")
        self.assertEqual(root.evephone, "867-5309")
        self.assertEqual(root.email, "test@example.com")
        self.assertEqual(root.dtinfochg, datetime(2014, 11, 22, tzinfo=UTC))


class ChguserinfotrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = ChguserinforqTestCase


class ChguserinfotrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ChguserinforsTestCase


class ChguserinfosyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        trnrq = ChguserinfotrnrqTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrq))
                yield root


class ChguserinfosyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        trnrs = ChguserinfotrnrsTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root


if __name__ == "__main__":
    unittest.main()
