# coding: utf-8
""" Unit tests for ofxtools.models.signup """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
import itertools


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.signup import (
    ACCTINFO,
    ACCTINFORQ,
    ACCTINFORS,
    ACCTINFOTRNRQ,
    ACCTINFOTRNRS,
    ENROLLRQ,
    ENROLLRS,
    ENROLLTRNRQ,
    ENROLLTRNRS,
    SVCS,
    SVCADD,
    SVCCHG,
    SVCDEL,
    ACCTRQ,
    ACCTRS,
    ACCTTRNRQ,
    ACCTTRNRS,
    ACCTSYNCRQ,
    ACCTSYNCRS,
    CHGUSERINFORQ,
    CHGUSERINFORS,
    CHGUSERINFOTRNRQ,
    CHGUSERINFOTRNRS,
    CHGUSERINFOSYNCRQ,
    CHGUSERINFOSYNCRS,
    CLIENTENROLL,
    WEBENROLL,
    OTHERENROLL,
)
from ofxtools.utils import UTC, classproperty
from ofxtools.models.i18n import COUNTRY_CODES


# test imports
import base
import test_models_bank_stmt as bk_stmt
import test_models_invest as invest


class ClientenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ACCTREQUIRED"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CLIENTENROLL")
        SubElement(root, "ACCTREQUIRED").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CLIENTENROLL(acctrequired=True)


class WebenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["URL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WEBENROLL")
        SubElement(root, "URL").text = "http://www.ameritrade.com"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WEBENROLL(url="http://www.ameritrade.com")


class OtherenrollTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MESSAGE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("OTHERENROLL")
        SubElement(root, "MESSAGE").text = "Mail me $99.99"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return OTHERENROLL(message="Mail me $99.99")


class AcctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ["DESC", "PHONE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTINFO")
        SubElement(root, "DESC").text = "All accounts"
        SubElement(root, "PHONE").text = "8675309"
        bankacctinfo = bk_stmt.BankacctinfoTestCase.etree
        root.append(bankacctinfo)
        ccacctinfo = bk_stmt.CcacctinfoTestCase.etree
        root.append(ccacctinfo)
        invacctinfo = invest.InvacctinfoTestCase.etree
        root.append(invacctinfo)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTINFO(
            bk_stmt.BankacctinfoTestCase.aggregate,
            bk_stmt.CcacctinfoTestCase.aggregate,
            invest.InvacctinfoTestCase.aggregate,
            desc="All accounts",
            phone="8675309",
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        # Any order of *ACCTINFO is OK
        acctinfos = [
            bk_stmt.BankacctinfoTestCase,
            bk_stmt.CcacctinfoTestCase,
            invest.InvacctinfoTestCase,
        ]
        for seq in itertools.permutations(acctinfos):
            root = Element("ACCTINFO")
            SubElement(root, "DESC").text = "All accounts"
            SubElement(root, "PHONE").text = "8675309"
            for acctinfo in seq:
                root.append(acctinfo.etree)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Missing *ACCTINFO
        root = Element("ACCTINFO")
        SubElement(root, "DESC").text = "All accounts"
        SubElement(root, "PHONE").text = "8675309"
        yield root

        acctinfos = [
            bk_stmt.BankacctinfoTestCase,
            bk_stmt.CcacctinfoTestCase,
            invest.InvacctinfoTestCase,
        ]

        # Two of the same *ACCTINFO
        for seq in itertools.permutations(acctinfos):
            seq = list(seq)
            doubleMe = seq[0].etree
            root = Element("ACCTINFO")
            SubElement(root, "DESC").text = "All accounts"
            SubElement(root, "PHONE").text = "8675309"
            root.append(doubleMe)
            root.append(doubleMe)
            for acctinfo in [None] + seq[1:]:
                if acctinfo is not None:
                    root.append(acctinfo.etree)
            yield root

    def testRepr(self):
        rep = repr(Aggregate.from_etree(self.etree))
        self.assertEqual(rep, ("<ACCTINFO desc='All accounts' phone='8675309' len=3>"))


class AcctinfoMalformedTestCase(unittest.TestCase):
    def testMissingXxxacctinfo(cls):
        root = Element("ACCTINFO")

        with cls.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleBankacctinfo(cls):
        root = Element("ACCTINFO")
        bankacctinfo = bk_stmt.BankacctinfoTestCase.etree
        root.append(bankacctinfo)
        root.append(bankacctinfo)

        with cls.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleCcacctinfo(cls):
        root = Element("ACCTINFO")
        ccacctinfo = bk_stmt.CcacctinfoTestCase.etree
        root.append(ccacctinfo)
        root.append(ccacctinfo)

        with cls.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testMultipleInvacctinfo(cls):
        root = Element("ACCTINFO")
        invacctinfo = invest.InvacctinfoTestCase.etree
        root.append(invacctinfo)
        root.append(invacctinfo)

        with cls.assertRaises(ValueError):
            Aggregate.from_etree(root)


class AcctinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTACCTUP"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTINFORQ")
        SubElement(root, "DTACCTUP").text = "20120314000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTINFORQ(dtacctup=datetime(2012, 3, 14, tzinfo=UTC))


class AcctinforsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTACCTUP"]
    optionalElements = ["ACCTINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTINFORS")
        SubElement(root, "DTACCTUP").text = "20120314000000.000[+0:UTC]"
        acctinfo = AcctinfoTestCase.etree
        root.append(acctinfo)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTINFORS(
            AcctinfoTestCase.aggregate, dtacctup=datetime(2012, 3, 14, tzinfo=UTC)
        )

    def testRepr(self):
        rep = repr(Aggregate.from_etree(self.etree))
        self.assertEqual(rep, "<ACCTINFORS dtacctup='2012-03-14 00:00:00+00:00' len=1>")


class AcctinfotrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = AcctinforqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTINFOTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            acctinforq=AcctinforqTestCase.aggregate,
        )


class AcctinfotrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = AcctinforsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTINFOTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            acctinfors=AcctinforsTestCase.aggregate,
        )


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
    oneOfs = {"COUNTRY": COUNTRY_CODES}

    @classproperty
    @classmethod
    def emptyBase(cls):
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
        SubElement(root, "DATEBIRTH").text = "20160705000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def etree(cls):
        root = cls.emptyBase
        root.append(bk_stmt.BankacctfromTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ENROLLRQ(
            firstname="Porky",
            middlename="D.",
            lastname="Pig",
            addr1="3717 N Clark St",
            addr2="Dugout Box, Aisle 19",
            addr3="Seat A1",
            city="Chicago",
            state="IL",
            postalcode="60613",
            country="USA",
            dayphone="(773) 309-1027",
            evephone="867-5309",
            email="spam@null.void",
            userid="bacon2b",
            taxid="123456789",
            securityname="Petunia",
            datebirth=datetime(2016, 7, 5, tzinfo=UTC),
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        root = cls.emptyBase
        yield root
        for acctfrom in (
            bk_stmt.BankacctfromTestCase,
            bk_stmt.CcacctfromTestCase,
            invest.InvacctfromTestCase,
        ):
            root = cls.emptyBase
            root.append(acctfrom.etree)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [
        #  ("bankacctfrom", "ccacctfrom"),
        #  ("bankacctfrom", "invacctfrom"),
        #  ("ccacctfrom", "invacctfrom"),
        #  ]
        acctfroms = [
            bk_stmt.BankacctfromTestCase,
            bk_stmt.CcacctfromTestCase,
            invest.InvacctfromTestCase,
        ]
        # Two of the same *ACCTFROM
        for acctfrom in acctfroms:
            root = cls.emptyBase
            root.append(acctfrom.etree)
            root.append(acctfrom.etree)
            yield root

        # Two different *ACCTFROM
        for seq in itertools.permutations(acctfroms):
            root = cls.emptyBase
            for acctfrom in list(seq)[1:]:
                root.append(acctfrom.etree)
            yield root

        # All three *ACCTFROM types
        root = cls.emptyBase
        for acctfrom in acctfroms:
            root.append(acctfrom.etree)
        yield root


class EnrollrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ["TEMPPASS", "USERID", "DTEXPIRE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ENROLLRS")
        SubElement(root, "TEMPPASS").text = "t0ps3kr1t"
        SubElement(root, "USERID").text = "bacon2b"
        SubElement(root, "DTEXPIRE").text = "20160705000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ENROLLRS(
            temppass="t0ps3kr1t",
            userid="bacon2b",
            dtexpire=datetime(2016, 7, 5, tzinfo=UTC),
        )


class EnrolltrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = EnrollrqTestCase

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ENROLLTRNRQ")
        SubElement(root, "TRNUID").text = "DEADBEEF"
        SubElement(root, "CLTCOOKIE").text = "B00B135"
        SubElement(root, "TAN").text = "B16B00B5"
        root.append(EnrollrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ENROLLTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            enrollrq=EnrollrqTestCase.aggregate,
        )


class EnrolltrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = EnrollrsTestCase

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ENROLLTRNRS")
        SubElement(root, "TRNUID").text = "DEADBEEF"
        root.append(base.StatusTestCase.etree)
        SubElement(root, "CLTCOOKIE").text = "B00B135"
        root.append(EnrollrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ENROLLTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            enrollrs=EnrollrsTestCase.aggregate,
        )


class SvcaddTestCase(unittest.TestCase, base.TestAggregate):
    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SVCADD")
        acctto = bk_stmt.BankaccttoTestCase.etree
        root.append(acctto)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SVCADD(bankacctto=bk_stmt.BankaccttoTestCase.aggregate)

    @classproperty
    @classmethod
    def validSoup(cls):
        accttos = [
            bk_stmt.BankaccttoTestCase,
            bk_stmt.CcaccttoTestCase,
            invest.InvaccttoTestCase,
        ]
        for acctto in accttos:
            root = Element("SVCADD")
            root.append(acctto.etree)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [("bankacctto", "ccacctto", "invacctto")]

        # No *ACCTTO
        yield Element("SVCADD")

        # Two of the same *ACCTTO
        accttos = [
            bk_stmt.BankaccttoTestCase,
            bk_stmt.CcaccttoTestCase,
            invest.InvaccttoTestCase,
        ]
        for acctto in accttos:
            root = Element("SVCADD")
            root.append(acctto.etree)
            root.append(acctto.etree)
            yield root

        # Two different *ACCTO
        for seq in itertools.permutations(accttos):
            root = Element("SVCADD")
            for acctto in list(seq)[1:]:
                root.append(acctto.etree)
            yield root

        # All three *ACCTO types
        root = Element("SVCADD")
        for acctto in accttos:
            root.append(acctto.etree)
        yield root


class SvcchgTestCase(unittest.TestCase, base.TestAggregate):
    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SVCCHG")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        root.append(bk_stmt.BankaccttoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SVCCHG(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            bankacctto=bk_stmt.BankaccttoTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        acctfroms = [
            bk_stmt.BankacctfromTestCase,
            bk_stmt.CcacctfromTestCase,
            invest.InvacctfromTestCase,
        ]
        accttos = [
            bk_stmt.BankaccttoTestCase,
            bk_stmt.CcaccttoTestCase,
            invest.InvaccttoTestCase,
        ]
        for acctfrom in acctfroms:
            for acctto in accttos:
                root = Element("SVCCHG")
                root.append(acctfrom.etree)
                root.append(acctto.etree)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [
        #  ("bankacctfrom", "ccacctfrom", "invacctfrom"),
        #  ("bankacctto", "ccacctto", "invacctto"),
        #  ]

        # No *ACCTFROM or *ACCTTO
        yield Element("SVCCHG")

        acctfroms = [
            bk_stmt.BankacctfromTestCase,
            bk_stmt.CcacctfromTestCase,
            invest.InvacctfromTestCase,
        ]
        accttos = [
            bk_stmt.BankaccttoTestCase,
            bk_stmt.CcaccttoTestCase,
            invest.InvaccttoTestCase,
        ]

        # *ACCTFROM with no *ACCTTO
        for acctfrom in acctfroms:
            root = Element("SVCCHG")
            root.append(acctfrom.etree)
            yield root

        # *ACCTTO with no *ACCTFROM
        for acctto in accttos:
            root = Element("SVCCHG")
            root.append(acctto.etree)
            yield root

        # Two of the same *ACCTFROM
        for acctfrom in acctfroms:
            for acctto in [None] + accttos:
                root = Element("SVCCHG")
                root.append(acctfrom.etree)
                root.append(acctfrom.etree)
                if acctto is not None:
                    root.append(acctto.etree)
                yield root

        # Two of the same *ACCTTO
        for acctfrom in [None] + acctfroms:
            root = Element("SVCCHG")
            if acctfrom is not None:
                root.append(acctfrom.etree)
            for acctto in accttos:
                root.append(acctto.etree)
                root.append(acctto.etree)
                yield root

        # Two different *ACCTFROM
        for acctto in [None] + accttos:
            for seq in itertools.permutations(acctfroms):
                root = Element("SVCCHG")
                for acctfrom in list(seq)[1:]:
                    root.append(acctfrom.etree)
                if acctto is not None:
                    root.append(acctto.etree)
                yield root

        # Two different *ACCTTO
        for acctfrom in [None] + acctfroms:
            for seq in itertools.permutations(accttos):
                root = Element("SVCCHG")
                if acctfrom is not None:
                    root.append(acctfrom.etree)
                for acctto in list(seq)[1:]:
                    root.append(acctto.etree)
                yield root

        # All three *ACCTFROM types
        for acctto in accttos:
            root = Element("SVCCHG")
            for acctfrom in acctfroms:
                root.append(acctfrom.etree)
            root.append(acctto.etree)
            yield root

        # All three *ACCTO types
        for acctfrom in acctfroms:
            root = Element("SVCCHG")
            root.append(acctfrom.etree)
            for acctto in accttos:
                root.append(acctto.etree)
            yield root


class SvcdelTestCase(unittest.TestCase, base.TestAggregate):
    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SVCDEL")
        acctfrom = bk_stmt.BankacctfromTestCase.etree
        root.append(acctfrom)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SVCDEL(bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate)

    @classproperty
    @classmethod
    def validSoup(cls):
        acctfroms = [
            bk_stmt.BankacctfromTestCase,
            bk_stmt.CcacctfromTestCase,
            invest.InvacctfromTestCase,
        ]
        for acctfrom in acctfroms:
            root = Element("SVCDEL")
            root.append(acctfrom.etree)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [("bankacctfrom", "ccacctfrom", "invacctfrom")]

        # No *ACCTTO
        yield Element("SVCDEL")

        # Two of the same *ACCTFROM
        acctfroms = [
            bk_stmt.BankacctfromTestCase,
            bk_stmt.CcacctfromTestCase,
            invest.InvacctfromTestCase,
        ]
        for acctfrom in acctfroms:
            root = Element("SVCDEL")
            root.append(acctfrom.etree)
            root.append(acctfrom.etree)
            yield root

        # Two different *ACCTFROM
        for seq in itertools.permutations(acctfroms):
            root = Element("SVCDEL")
            for acctfrom in list(seq)[1:]:
                root.append(acctfrom.etree)
            yield root

        # All three *ACCFROM types
        root = Element("SVCDEL")
        for acctfrom in acctfroms:
            root.append(acctfrom.etree)
        yield root


class AcctrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SVC"]
    oneOfs = {"SVC": SVCS}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTRQ")
        root.append(SvcaddTestCase.etree)
        SubElement(root, "SVC").text = "BANKSVC"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTRQ(svcadd=SvcaddTestCase.aggregate, svc="BANKSVC")

    @classproperty
    @classmethod
    def validSoup(cls):
        for svcaction in SvcaddTestCase, SvcchgTestCase, SvcdelTestCase:
            root = Element("ACCTRQ")
            root.append(svcaction.etree)
            SubElement(root, "SVC").text = "BANKSVC"
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [("svcadd", "svcchg", "svcdel")]
        svcactions = [SvcaddTestCase, SvcchgTestCase, SvcdelTestCase]

        # No SVC*
        root = Element("ACCTRQ")
        SubElement(root, "SVC").text = "BANKSVC"
        yield root

        # Two of the same SVC*
        for svcaction in svcactions:
            root = Element("ACCTRQ")
            root.append(svcaction.etree)
            root.append(svcaction.etree)
            SubElement(root, "SVC").text = "BANKSVC"
            yield root

        # Two different SVC*
        for seq in itertools.permutations(svcactions):
            root = Element("ACCTRQ")
            for svcaction in list(seq)[1:]:
                root.append(svcaction.etree)
            SubElement(root, "SVC").text = "BANKSVC"
            yield root

        # All three SVC*
        root = Element("ACCTRQ")
        for svcaction in svcactions:
            root.append(svcaction.etree)
        SubElement(root, "SVC").text = "BANKSVC"
        yield root


class AcctrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SVC", "SVCSTATUS"]
    oneOfs = {"SVC": SVCS, "SVCSTATUS": SVCSTATUSES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTRS")
        root.append(SvcaddTestCase.etree)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTRS(svcadd=SvcaddTestCase.aggregate, svc="BANKSVC", svcstatus="AVAIL")

    @classproperty
    @classmethod
    def validSoup(cls):
        for svcaction in SvcaddTestCase, SvcchgTestCase, SvcdelTestCase:
            root = Element("ACCTRS")
            root.append(svcaction.etree)
            SubElement(root, "SVC").text = "BANKSVC"
            SubElement(root, "SVCSTATUS").text = "AVAIL"
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [("svcadd", "svcchg", "svcdel")]
        svcactions = [SvcaddTestCase, SvcchgTestCase, SvcdelTestCase]

        # No SVC*
        root = Element("ACCTRS")
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        yield root

        # Two of the same SVC*
        for svcaction in svcactions:
            root = Element("ACCTRS")
            root.append(svcaction.etree)
            root.append(svcaction.etree)
            SubElement(root, "SVC").text = "BANKSVC"
            SubElement(root, "SVCSTATUS").text = "AVAIL"
            yield root

        # Two different SVC*
        for seq in itertools.permutations(svcactions):
            root = Element("ACCTRS")
            for svcaction in list(seq)[1:]:
                root.append(svcaction.etree)
            SubElement(root, "SVC").text = "BANKSVC"
            SubElement(root, "SVCSTATUS").text = "AVAIL"
            yield root

        # All three SVC*
        root = Element("ACCTRS")
        for svcaction in svcactions:
            root.append(svcaction.etree)
        SubElement(root, "SVC").text = "BANKSVC"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        yield root


class AccttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = AcctrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            acctrq=AcctrqTestCase.aggregate,
        )


class AccttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = AcctrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            acctrs=AcctrsTestCase.aggregate,
        )


class AcctsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(AccttrnrqTestCase.etree)
        root.append(AccttrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTSYNCRQ(
            AccttrnrqTestCase.aggregate,
            AccttrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(AccttrnrqTestCase.etree)
                yield root


class AcctsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("ACCTSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(AccttrnrsTestCase.etree)
        root.append(AccttrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ACCTSYNCRS(
            AccttrnrsTestCase.aggregate,
            AccttrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(AccttrnrsTestCase.etree)
                yield root


class ChguserinforqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

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

    @classproperty
    @classmethod
    def etree(cls):
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

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHGUSERINFORQ(
            firstname="Mary",
            middlename="J.",
            lastname="Blige",
            addr1="3717 N Clark St",
            addr2="Dugout Box, Aisle 19",
            addr3="Seat A1",
            city="Chicago",
            state="IL",
            postalcode="60613",
            country="USA",
            dayphone="(773) 309-1027",
            evephone="867-5309",
            email="test@example.com",
        )


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

    @classproperty
    @classmethod
    def etree(cls):
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
        SubElement(root, "DTINFOCHG").text = "20141122000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHGUSERINFORS(
            firstname="Mary",
            middlename="J.",
            lastname="Blige",
            addr1="3717 N Clark St",
            addr2="Dugout Box, Aisle 19",
            addr3="Seat A1",
            city="Chicago",
            state="IL",
            postalcode="60613",
            country="USA",
            dayphone="(773) 309-1027",
            evephone="867-5309",
            email="test@example.com",
            dtinfochg=datetime(2014, 11, 22, tzinfo=UTC),
        )


class ChguserinfotrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = ChguserinforqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHGUSERINFOTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            chguserinforq=ChguserinforqTestCase.aggregate,
        )


class ChguserinfotrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ChguserinforsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHGUSERINFOTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            chguserinfors=ChguserinforsTestCase.aggregate,
        )


class ChguserinfosyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CHGUSERINFOSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(ChguserinfotrnrqTestCase.etree)
        root.append(ChguserinfotrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHGUSERINFOSYNCRQ(
            ChguserinfotrnrqTestCase.aggregate,
            ChguserinfotrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(ChguserinfotrnrqTestCase.etree)
                yield root


class ChguserinfosyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CHGUSERINFOSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(ChguserinfotrnrsTestCase.etree)
        root.append(ChguserinfotrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHGUSERINFOSYNCRS(
            ChguserinfotrnrsTestCase.aggregate,
            ChguserinfotrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(ChguserinfotrnrsTestCase.etree)
                yield root


if __name__ == "__main__":
    unittest.main()
