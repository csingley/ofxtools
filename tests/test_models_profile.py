# coding: utf-8
""" Unit tests for models.profile """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime, time
from decimal import Decimal
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import OFXEXTENSION
from ofxtools.models.email import (
    EMAILMSGSRQV1,
    EMAILMSGSRSV1,
    EMAILMSGSETV1,
    EMAILMSGSET,
    MAILTRNRQ,
    MAILTRNRS,
    GETMIMETRNRQ,
    GETMIMETRNRS,
    MAILSYNCRQ,
    MAILSYNCRS,
)
from ofxtools.models.profile import (
    PROFRQ,
    PROFRS,
    PROFTRNRQ,
    PROFTRNRS,
    MSGSETLIST,
    SIGNONINFOLIST,
    PROFMSGSRQV1,
    PROFMSGSRSV1,
    PROFMSGSETV1,
    PROFMSGSET,
)
from ofxtools.models.signon import SIGNONINFO, SIGNONMSGSETV1, SIGNONMSGSET
from ofxtools.models.signup import SIGNUPMSGSETV1, SIGNUPMSGSET, WEBENROLL
from ofxtools.models.bank.stmt import (
    ACCTTYPES,
    STMTRS,
    STMTTRNRQ,
    STMTTRNRS,
    CCSTMTTRNRQ,
    CCSTMTTRNRS,
)
from ofxtools.models.bank.stmtend import (
    STMTENDTRNRQ,
    STMTENDTRNRS,
    CCSTMTENDTRNRQ,
    CCSTMTENDTRNRS,
)
from ofxtools.models.bank.stpchk import STPCHKTRNRQ, STPCHKTRNRS
from ofxtools.models.bank.msgsets import (
    XFERPROF,
    STPCHKPROF,
    EMAILPROF,
    BANKMSGSRQV1,
    BANKMSGSRSV1,
    BANKMSGSETV1,
    BANKMSGSET,
    CREDITCARDMSGSRQV1,
    CREDITCARDMSGSRSV1,
    CREDITCARDMSGSETV1,
    CREDITCARDMSGSET,
    INTERXFERMSGSRQV1,
    INTERXFERMSGSRSV1,
    INTERXFERMSGSETV1,
    INTERXFERMSGSET,
    WIREXFERMSGSRQV1,
    WIREXFERMSGSRSV1,
    WIREXFERMSGSETV1,
    WIREXFERMSGSET,
)
from ofxtools.models.bank.intraxfer import INTRATRNRQ, INTRATRNRS
from ofxtools.models.bank.interxfer import INTERTRNRQ, INTERTRNRS
from ofxtools.models.bank.wire import WIRETRNRQ, WIRETRNRS
from ofxtools.models.bank.recur import (
    RECINTRATRNRQ,
    RECINTRATRNRS,
    RECINTERTRNRQ,
    RECINTERTRNRS,
)
from ofxtools.models.bank.mail import BANKMAILTRNRQ, BANKMAILTRNRS
from ofxtools.models.bank.sync import (
    STPCHKSYNCRQ,
    STPCHKSYNCRS,
    INTRASYNCRQ,
    INTRASYNCRS,
    INTERSYNCRQ,
    INTERSYNCRS,
    WIRESYNCRQ,
    WIRESYNCRS,
    RECINTRASYNCRQ,
    RECINTRASYNCRS,
    RECINTERSYNCRQ,
    RECINTERSYNCRS,
    BANKMAILSYNCRQ,
    BANKMAILSYNCRS,
)
from ofxtools.models.investment import INVSTMTMSGSETV1, INVSTMTMSGSET
from ofxtools.models.seclist import SECLISTMSGSETV1, SECLISTMSGSET
from ofxtools.models.profile import MSGSETCORE
from ofxtools.models.i18n import LANG_CODES
from ofxtools.models.tax1099 import TAX1099MSGSETV1, TAX1099MSGSET
from ofxtools.utils import UTC


# test imports
import base
from test_models_common import OfxextensionTestCase
from test_models_email import (
    MailtrnrqTestCase,
    MailtrnrsTestCase,
    GetmimetrnrqTestCase,
    GetmimetrnrsTestCase,
    MailsyncrqTestCase,
    MailsyncrsTestCase,
)
from test_models_bank_stmt import (
    BankacctfromTestCase,
    StmttrnrqTestCase,
    StmttrnrsTestCase,
    CcstmttrnrqTestCase,
    CcstmttrnrsTestCase,
)
from test_models_bank_stmtend import (
    StmtendtrnrqTestCase,
    StmtendtrnrsTestCase,
    CcstmtendtrnrqTestCase,
    CcstmtendtrnrsTestCase,
)
from test_models_bank_stpchk import StpchktrnrqTestCase, StpchktrnrsTestCase
from test_models_bank_intraxfer import IntratrnrqTestCase, IntratrnrsTestCase
from test_models_bank_interxfer import IntertrnrqTestCase, IntertrnrsTestCase
from test_models_bank_wire import WiretrnrqTestCase, WiretrnrsTestCase
from test_models_bank_recur import (
    RecintratrnrqTestCase,
    RecintratrnrsTestCase,
    RecintertrnrqTestCase,
    RecintertrnrsTestCase,
)
from test_models_bank_mail import BankmailtrnrqTestCase, BankmailtrnrsTestCase
from test_models_bank_sync import (
    StpchksyncrqTestCase,
    StpchksyncrsTestCase,
    IntrasyncrqTestCase,
    IntrasyncrsTestCase,
    IntersyncrqTestCase,
    IntersyncrsTestCase,
    RecintrasyncrqTestCase,
    RecintrasyncrsTestCase,
    RecintersyncrqTestCase,
    RecintersyncrsTestCase,
    BankmailsyncrqTestCase,
    BankmailsyncrsTestCase,
)
from test_models_signup import WebenrollTestCase


class ProfrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CLIENTROUTING", "DTPROFUP"]

    @property
    def root(self):
        root = Element("PROFRQ")
        SubElement(root, "CLIENTROUTING").text = "SERVICE"
        SubElement(root, "DTPROFUP").text = "20010401"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFRQ)
        self.assertEqual(root.clientrouting, "SERVICE")
        self.assertEqual(root.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest("CLIENTROUTING", ("NONE", "SERVICE", "MSGSET"))


class ProftrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = ProfrqTestCase


# Go aheand and define all *MSGSET test cases here to avoid circular imports
class SignoninfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "SIGNONREALM",
        "MIN",
        "MAX",
        "CHARTYPE",
        "CASESEN",
        "SPECIAL",
        "SPACES",
        "PINCH",
    ]
    # optionalElements = ['CHGPINFIRST', 'USERCRED1LABEL', 'USERCRED2LABEL',
    # 'CLIENTUIDREQ', 'AUTHTOKENFIRST', 'AUTHTOKENLABEL',
    # 'AUTHTOKENINFOURL', 'MFACHALLENGESUPT',
    # 'MFACHALLENGEFIRST', 'ACCESSTOKENREQ', ]

    @property
    def root(self):
        root = Element("SIGNONINFO")
        SubElement(root, "SIGNONREALM").text = "AMERITRADE"
        SubElement(root, "MIN").text = "4"
        SubElement(root, "MAX").text = "32"
        SubElement(root, "CHARTYPE").text = "ALPHAORNUMERIC"
        SubElement(root, "CASESEN").text = "Y"
        SubElement(root, "SPECIAL").text = "N"
        SubElement(root, "SPACES").text = "N"
        SubElement(root, "PINCH").text = "N"
        SubElement(root, "CHGPINFIRST").text = "N"
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
        self.assertEqual(root.signonrealm, "AMERITRADE")
        self.assertEqual(root.min, 4)
        self.assertEqual(root.max, 32)
        self.assertEqual(root.chartype, "ALPHAORNUMERIC")
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
        self.oneOfTest(
            "CHARTYPE",
            ("ALPHAONLY", "NUMERICONLY", "ALPHAORNUMERIC", "ALPHAANDNUMERIC"),
        )


class SignoninfolistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SIGNONINFOLIST")
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


class ProfrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "MSGSETLIST",
        "SIGNONINFOLIST",
        "DTPROFUP",
        "FINAME",
        "ADDR1",
        "CITY",
        "STATE",
        "POSTALCODE",
        "COUNTRY",
    ]
    optionalElements = [
        "ADDR2",
        "ADDR3",
        "CSPHONE",
        "TSPHONE",
        "FAXPHONE",
        "URL",
        "EMAIL",
    ]

    @property
    def root(self):
        root = Element("PROFRS")
        msgsetlist = MsgsetlistTestCase().root
        root.append(msgsetlist)
        signoninfolist = SignoninfolistTestCase().root
        root.append(signoninfolist)
        SubElement(root, "DTPROFUP").text = "20010401"
        SubElement(root, "FINAME").text = "Dewey Cheatham & Howe"
        SubElement(root, "ADDR1").text = "3717 N Clark St"
        SubElement(root, "ADDR2").text = "Dugout Box, Aisle 19"
        SubElement(root, "ADDR3").text = "Seat A1"
        SubElement(root, "CITY").text = "Chicago"
        SubElement(root, "STATE").text = "IL"
        SubElement(root, "POSTALCODE").text = "60613"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "CSPHONE").text = "(773) 309-1027"
        SubElement(root, "TSPHONE").text = "(773) 309-1028"
        SubElement(root, "FAXPHONE").text = "(773) 309-1029"
        SubElement(root, "URL").text = "http://www.ameritrade.com"
        SubElement(root, "EMAIL").text = "support@ameritrade.com"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFRS)
        self.assertIsInstance(root.msgsetlist, MSGSETLIST)
        self.assertIsInstance(root.signoninfolist, SIGNONINFOLIST)
        self.assertEqual(root.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))
        self.assertEqual(root.finame, "Dewey Cheatham & Howe")
        self.assertEqual(root.addr1, "3717 N Clark St")
        self.assertEqual(root.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(root.addr3, "Seat A1")
        self.assertEqual(root.city, "Chicago")
        self.assertEqual(root.state, "IL")
        self.assertEqual(root.postalcode, "60613")
        self.assertEqual(root.country, "USA")
        self.assertEqual(root.csphone, "(773) 309-1027")
        self.assertEqual(root.tsphone, "(773) 309-1028")
        self.assertEqual(root.faxphone, "(773) 309-1029")
        self.assertEqual(root.url, "http://www.ameritrade.com")
        self.assertEqual(root.email, "support@ameritrade.com")

    def testConvertRemoveProprietaryTag(self):
        # Make sure SONRS.from_etree() removes proprietary tags
        root = deepcopy(self.root)
        SubElement(root, "INTU.BANKID").text = "12345678"

        profrs = Aggregate.from_etree(root)
        self.assertIsInstance(profrs, PROFRS)
        # Converted Aggregate should still have 16 values, not 17
        self.assertEqual(len(profrs._spec_repr), 16)

        self.assertIsInstance(profrs.msgsetlist, MSGSETLIST)
        self.assertIsInstance(profrs.signoninfolist, SIGNONINFOLIST)
        self.assertEqual(profrs.dtprofup, datetime(2001, 4, 1, tzinfo=UTC))
        self.assertEqual(profrs.finame, "Dewey Cheatham & Howe")
        self.assertEqual(profrs.addr1, "3717 N Clark St")
        self.assertEqual(profrs.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(profrs.addr3, "Seat A1")
        self.assertEqual(profrs.city, "Chicago")
        self.assertEqual(profrs.state, "IL")
        self.assertEqual(profrs.postalcode, "60613")
        self.assertEqual(profrs.country, "USA")
        self.assertEqual(profrs.csphone, "(773) 309-1027")
        self.assertEqual(profrs.tsphone, "(773) 309-1028")
        self.assertEqual(profrs.faxphone, "(773) 309-1029")
        self.assertEqual(profrs.url, "http://www.ameritrade.com")
        self.assertEqual(profrs.email, "support@ameritrade.com")


class ProftrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ProfrsTestCase

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        profile = instance.profile
        self.assertIsInstance(profile, PROFRS)


class MsgsetcoreTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "VER",
        "URL",
        "OFXSEC",
        "TRANSPSEC",
        "SIGNONREALM",
        "LANGUAGE",
        "SYNCMODE",
        "RESPFILEER",
    ]
    # optionalElements = ['REFRESHSUPT', 'SPNAME', 'OFXEXTENSION']

    @property
    def root(self):
        root = Element("MSGSETCORE")
        SubElement(root, "VER").text = "1"
        SubElement(root, "URL").text = "https://ofxs.ameritrade.com/cgi-bin/apps/OFX"
        SubElement(root, "OFXSEC").text = "NONE"
        SubElement(root, "TRANSPSEC").text = "Y"
        SubElement(root, "SIGNONREALM").text = "AMERITRADE"
        SubElement(root, "LANGUAGE").text = "ENG"
        SubElement(root, "SYNCMODE").text = "FULL"
        SubElement(root, "REFRESHSUPT").text = "N"
        SubElement(root, "RESPFILEER").text = "N"
        SubElement(root, "INTU.TIMEOUT").text = "360"
        SubElement(root, "SPNAME").text = "Dewey Cheatham & Howe"
        ofxextension = OfxextensionTestCase().root
        root.append(ofxextension)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MSGSETCORE)
        self.assertEqual(root.ver, 1)
        self.assertEqual(root.url, "https://ofxs.ameritrade.com/cgi-bin/apps/OFX")
        self.assertEqual(root.ofxsec, "NONE")
        self.assertEqual(root.transpsec, True)
        self.assertEqual(root.signonrealm, "AMERITRADE")
        self.assertEqual(root.language, "ENG")
        self.assertEqual(root.syncmode, "FULL")
        self.assertEqual(root.refreshsupt, False)
        self.assertEqual(root.respfileer, False)
        self.assertEqual(root.spname, "Dewey Cheatham & Howe")
        self.assertIsInstance(root.ofxextension, OFXEXTENSION)

    def testOneOf(self):
        self.oneOfTest("OFXSEC", ("NONE", "TYPE1"))
        self.oneOfTest("LANGUAGE", LANG_CODES)
        self.oneOfTest("SYNCMODE", ("FULL", "LITE"))


class Emailmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILMSGSRQV1")
        for rq in (MailtrnrqTestCase, GetmimetrnrqTestCase, MailsyncrqTestCase):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # EMAILMSGSRQV1 may contain ["MAILTRNRQ", "GETMIMETRNRQ", "MAILSYNCRQ"]

        allowedTags = EMAILMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 3)
        root = deepcopy(self.root)
        root.append(MailtrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, EMAILMSGSRQV1)
        self.assertEqual(len(instance), 6)
        self.assertIsInstance(instance[0], MAILTRNRQ)
        self.assertIsInstance(instance[1], MAILTRNRQ)
        self.assertIsInstance(instance[2], GETMIMETRNRQ)
        self.assertIsInstance(instance[3], GETMIMETRNRQ)
        self.assertIsInstance(instance[4], MAILSYNCRQ)
        self.assertIsInstance(instance[5], MAILSYNCRQ)


class Emailmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILMSGSRSV1")
        for rs in (MailtrnrsTestCase, GetmimetrnrsTestCase, MailsyncrsTestCase):
            for i in range(2):
                root.append(rs().root)
        return root

    def testdataTags(self):
        # EMAILMSGSRSV1 may contain ["MAILTRNRS", "GETMIMETRNRS", "MAILSYNCRS"]

        allowedTags = EMAILMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 3)
        root = deepcopy(self.root)
        root.append(MailtrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, EMAILMSGSRSV1)
        self.assertEqual(len(instance), 6)
        self.assertIsInstance(instance[0], MAILTRNRS)
        self.assertIsInstance(instance[1], MAILTRNRS)
        self.assertIsInstance(instance[2], GETMIMETRNRS)
        self.assertIsInstance(instance[3], GETMIMETRNRS)
        self.assertIsInstance(instance[4], MAILSYNCRS)
        self.assertIsInstance(instance[5], MAILSYNCRS)


class Emailmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "MAILSUP").text = "Y"
        SubElement(root, "GETMIMESUP").text = "Y"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, EMAILMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.mailsup, True)
        self.assertEqual(root.getmimesup, True)


class EmailmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILMSGSET")
        msgsetv1 = Emailmsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, EMAILMSGSET)
        self.assertIsInstance(root.emailmsgsetv1, EMAILMSGSETV1)


class Bankmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSRQV1")
        for rq in (
            StmttrnrqTestCase,
            StmtendtrnrqTestCase,
            StpchktrnrqTestCase,
            IntratrnrqTestCase,
            RecintratrnrqTestCase,
            BankmailtrnrqTestCase,
            StpchksyncrqTestCase,
            IntrasyncrqTestCase,
            RecintrasyncrqTestCase,
            BankmailsyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # BANKMSGSRQV1 may contain
        # ["STMTTRNRQ", "STMTENDTRNRQ", "STPCHKTRNRQ", "INTRATRNRQ",
        # "RECINTRATRNRQ", "BANKMAILTRNRQ", "STPCHKSYNCRQ", "INTRASYNCRQ",
        # "RECINTRASYNCRQ", "BANKMAILSYNCRQ"]

        allowedTags = BANKMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 10)
        root = deepcopy(self.root)
        root.append(StmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BANKMSGSRQV1)
        self.assertEqual(len(instance), 20)
        self.assertIsInstance(instance[0], STMTTRNRQ)
        self.assertIsInstance(instance[1], STMTTRNRQ)
        self.assertIsInstance(instance[2], STMTENDTRNRQ)
        self.assertIsInstance(instance[3], STMTENDTRNRQ)
        self.assertIsInstance(instance[4], STPCHKTRNRQ)
        self.assertIsInstance(instance[5], STPCHKTRNRQ)
        self.assertIsInstance(instance[6], INTRATRNRQ)
        self.assertIsInstance(instance[7], INTRATRNRQ)
        self.assertIsInstance(instance[8], RECINTRATRNRQ)
        self.assertIsInstance(instance[9], RECINTRATRNRQ)
        self.assertIsInstance(instance[10], BANKMAILTRNRQ)
        self.assertIsInstance(instance[11], BANKMAILTRNRQ)
        self.assertIsInstance(instance[12], STPCHKSYNCRQ)
        self.assertIsInstance(instance[13], STPCHKSYNCRQ)
        self.assertIsInstance(instance[14], INTRASYNCRQ)
        self.assertIsInstance(instance[15], INTRASYNCRQ)
        self.assertIsInstance(instance[16], RECINTRASYNCRQ)
        self.assertIsInstance(instance[17], RECINTRASYNCRQ)
        self.assertIsInstance(instance[18], BANKMAILSYNCRQ)
        self.assertIsInstance(instance[19], BANKMAILSYNCRQ)


class Bankmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSRSV1")
        for rs in (
            StmttrnrsTestCase,
            StmtendtrnrsTestCase,
            StpchktrnrsTestCase,
            IntratrnrsTestCase,
            RecintratrnrsTestCase,
            BankmailtrnrsTestCase,
            StpchksyncrsTestCase,
            IntrasyncrsTestCase,
            RecintrasyncrsTestCase,
            BankmailsyncrsTestCase,
        ):
            for i in range(2):
                root.append(rs().root)
        return root

    def testdataTags(self):
        # BANKMSGSRSV! may contain
        # dataTags = ["STMTTRNRS", "STMTENDRS", "STPCHKTRNRS", "INTRATRNRS",
        # "RECINTRATRNRS", "BANKMAILTRNRS", "STPCHKSYNCRS", "INTRASYNCRS",
        # "RECINTRASYNCRS", "BANKMAILSYNCRS"]
        allowedTags = BANKMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 10)
        root = deepcopy(self.root)
        root.append(StmttrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BANKMSGSRSV1)
        self.assertEqual(len(instance), 20)
        self.assertIsInstance(instance[0], STMTTRNRS)
        self.assertIsInstance(instance[1], STMTTRNRS)
        self.assertIsInstance(instance[2], STMTENDTRNRS)
        self.assertIsInstance(instance[3], STMTENDTRNRS)
        self.assertIsInstance(instance[4], STPCHKTRNRS)
        self.assertIsInstance(instance[5], STPCHKTRNRS)
        self.assertIsInstance(instance[6], INTRATRNRS)
        self.assertIsInstance(instance[7], INTRATRNRS)
        self.assertIsInstance(instance[8], RECINTRATRNRS)
        self.assertIsInstance(instance[9], RECINTRATRNRS)
        self.assertIsInstance(instance[10], BANKMAILTRNRS)
        self.assertIsInstance(instance[11], BANKMAILTRNRS)
        self.assertIsInstance(instance[12], STPCHKSYNCRS)
        self.assertIsInstance(instance[13], STPCHKSYNCRS)
        self.assertIsInstance(instance[14], INTRASYNCRS)
        self.assertIsInstance(instance[15], INTRASYNCRS)
        self.assertIsInstance(instance[16], RECINTRASYNCRS)
        self.assertIsInstance(instance[17], RECINTRASYNCRS)
        self.assertIsInstance(instance[18], BANKMAILSYNCRS)
        self.assertIsInstance(instance[19], BANKMAILSYNCRS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.statements, list)
        self.assertEqual(len(instance.statements), 2)
        self.assertIsInstance(instance.statements[0], STMTRS)
        self.assertIsInstance(instance.statements[1], STMTRS)


class XferprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("XFERPROF")
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "CANRECUR").text = "Y"
        SubElement(root, "CANMODXFER").text = "N"
        SubElement(root, "CANMODMDLS").text = "Y"
        SubElement(root, "MODELWND").text = "3"
        SubElement(root, "DAYSWITH").text = "2"
        SubElement(root, "DFLDAYSTOPAY").text = "4"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, XFERPROF)
        self.assertEqual(instance.procdaysoff, None)  # Unsupported
        self.assertEqual(instance.procendtm, time(17, 0, 0, tzinfo=UTC))
        self.assertEqual(instance.cansched, True)
        self.assertEqual(instance.canrecur, True)
        self.assertEqual(instance.canmodxfer, False)
        self.assertEqual(instance.canmodmdls, True)
        self.assertEqual(instance.modelwnd, 3)
        self.assertEqual(instance.dayswith, 2)
        self.assertEqual(instance.dfldaystopay, 4)


class StpchkprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("STPCHKPROF")
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000"
        SubElement(root, "CANUSERANGE").text = "Y"
        SubElement(root, "CANUSEDESC").text = "Y"
        SubElement(root, "STPCHKFEE").text = "30.1"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKPROF)
        self.assertEqual(instance.procdaysoff, None)  # Unsupported
        self.assertEqual(instance.procendtm, time(17, 0, 0, tzinfo=UTC))
        self.assertEqual(instance.canuserange, True)
        self.assertEqual(instance.canusedesc, True)
        self.assertEqual(instance.stpchkfee, Decimal("30.1"))


class EmailprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILPROF")
        SubElement(root, "CANEMAIL").text = "Y"
        SubElement(root, "CANNOTIFY").text = "N"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, EMAILPROF)
        self.assertEqual(instance.canemail, True)
        self.assertEqual(instance.cannotify, False)


class Bankmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "INVALIDACCTTYPE").text = "CHECKING"
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        SubElement(root, "PENDINGAVAIL").text = "N"
        xferprof = XferprofTestCase().root
        root.append(xferprof)
        stpchkprof = StpchkprofTestCase().root
        root.append(stpchkprof)
        emailprof = EmailprofTestCase().root
        root.append(emailprof)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.invalidaccttype, "CHECKING")
        self.assertEqual(root.closingavail, True)
        self.assertEqual(root.pendingavail, False)
        self.assertIsInstance(root.xferprof, XFERPROF)
        self.assertIsInstance(root.stpchkprof, STPCHKPROF)
        self.assertIsInstance(root.emailprof, EMAILPROF)

    def testOneOf(self):
        self.oneOfTest("INVALIDACCTTYPE", ACCTTYPES)


class BankmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSET")
        bankmsgsetv1 = Bankmsgsetv1TestCase().root
        root.append(bankmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSET)
        self.assertIsInstance(root.bankmsgsetv1, BANKMSGSETV1)


class Creditcardmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("CREDITCARDMSGSRQV1")
        ccstmttrnrq = CcstmttrnrqTestCase().root
        root.append(ccstmttrnrq)
        ccstmtendtrnrq = CcstmtendtrnrqTestCase().root
        root.append(ccstmtendtrnrq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRQV1)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], CCSTMTTRNRQ)
        self.assertIsInstance(root[1], CCSTMTENDTRNRQ)


class Creditcardmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("CREDITCARDMSGSRQV1")
        ccstmttrnrq = CcstmttrnrqTestCase().root
        root.append(ccstmttrnrq)
        ccstmtendtrnrq = CcstmtendtrnrqTestCase().root
        root.append(ccstmtendtrnrq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRQV1)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], CCSTMTTRNRQ)
        self.assertIsInstance(root[1], CCSTMTENDTRNRQ)


class Creditcardmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("CREDITCARDMSGSRSV1")
        ccstmttrnrs = CcstmttrnrsTestCase().root
        root.append(ccstmttrnrs)
        ccstmtendtrnrs = CcstmtendtrnrsTestCase().root
        root.append(ccstmtendtrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRSV1)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], CCSTMTTRNRS)
        self.assertIsInstance(root[1], CCSTMTENDTRNRS)


class Creditcardmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE", "CLOSINGAVAIL"]
    optionalElements = ["PENDINGAVAIL"]

    @property
    def root(self):
        root = Element("CREDITCARDMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        SubElement(root, "PENDINGAVAIL").text = "N"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.closingavail, True)
        self.assertEqual(root.pendingavail, False)


class CreditcardmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("CREDITCARDMSGSET")
        bankstmtmsgsetv1 = Creditcardmsgsetv1TestCase().root
        root.append(bankstmtmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSET)
        self.assertIsInstance(root.creditcardmsgsetv1, CREDITCARDMSGSETV1)


class Interxfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSRQV1")
        for rq in (
            IntertrnrqTestCase,
            RecintertrnrqTestCase,
            IntersyncrqTestCase,
            RecintersyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # INTERXFERMSGSRQV1 may contain
        # ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]
        allowedTags = INTERXFERMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 4)
        root = deepcopy(self.root)
        root.append(IntertrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERXFERMSGSRQV1)
        self.assertEqual(len(instance), 8)
        self.assertIsInstance(instance[0], INTERTRNRQ)
        self.assertIsInstance(instance[1], INTERTRNRQ)
        self.assertIsInstance(instance[2], RECINTERTRNRQ)
        self.assertIsInstance(instance[3], RECINTERTRNRQ)
        self.assertIsInstance(instance[4], INTERSYNCRQ)
        self.assertIsInstance(instance[5], INTERSYNCRQ)
        self.assertIsInstance(instance[6], RECINTERSYNCRQ)
        self.assertIsInstance(instance[7], RECINTERSYNCRQ)


class Interxfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSRSV1")
        for rq in (
            IntertrnrsTestCase,
            RecintertrnrsTestCase,
            IntersyncrsTestCase,
            RecintersyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # INTERXFERMSGSRSV1 may contain
        # ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]
        allowedTags = INTERXFERMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 4)
        root = deepcopy(self.root)
        root.append(IntertrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERXFERMSGSRSV1)
        self.assertEqual(len(instance), 8)
        self.assertIsInstance(instance[0], INTERTRNRS)
        self.assertIsInstance(instance[1], INTERTRNRS)
        self.assertIsInstance(instance[2], RECINTERTRNRS)
        self.assertIsInstance(instance[3], RECINTERTRNRS)
        self.assertIsInstance(instance[4], INTERSYNCRS)
        self.assertIsInstance(instance[5], INTERSYNCRS)
        self.assertIsInstance(instance[6], RECINTERSYNCRS)
        self.assertIsInstance(instance[7], RECINTERSYNCRS)


class Interxfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        xferprof = XferprofTestCase().root
        root.append(xferprof)
        SubElement(root, "CANBILLPAY").text = "Y"
        SubElement(root, "CANCWND").text = "2"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INTERXFERMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertIsInstance(root.xferprof, XFERPROF)
        self.assertEqual(root.canbillpay, True)
        self.assertEqual(root.cancwnd, 2)
        self.assertEqual(root.domxferfee, Decimal("7.50"))
        self.assertEqual(root.intlxferfee, Decimal("17.50"))


class InterxfermsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSET")
        msgsetv1 = Interxfermsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INTERXFERMSGSET)
        self.assertIsInstance(root.interxfermsgsetv1, INTERXFERMSGSETV1)


class WiresyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = WiretrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = IntratrnrsTestCase().root

        # SYNCRQ base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class WiresyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = WiretrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = WiretrnrsTestCase().root

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class Wirexfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRQV1")
        for rq in (WiretrnrqTestCase, WiresyncrqTestCase):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # WIREXFERMSGSRQV1 may contain
        # ["WIRETRNRQ", "WIREERSYNCRQ"]
        allowedTags = WIREXFERMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 2)
        root = deepcopy(self.root)
        root.append(WiretrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREXFERMSGSRQV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], WIRETRNRQ)
        self.assertIsInstance(instance[1], WIRETRNRQ)
        self.assertIsInstance(instance[2], WIRESYNCRQ)
        self.assertIsInstance(instance[3], WIRESYNCRQ)


class Wirexfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRSV1")
        for rq in (WiretrnrsTestCase, WiresyncrsTestCase):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # WIRERXFERMSGSRSV1 may contain
        # ["WIRETRNRS", "WIRESYNCRS"]
        allowedTags = WIREXFERMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 2)
        root = deepcopy(self.root)
        root.append(WiretrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREXFERMSGSRSV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], WIRETRNRS)
        self.assertIsInstance(instance[1], WIRETRNRS)
        self.assertIsInstance(instance[2], WIRESYNCRS)
        self.assertIsInstance(instance[3], WIRESYNCRS)


class Wirexfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, WIREXFERMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertIsNone(root.procdaysoff)  # Unsupported
        self.assertEqual(root.procendtm, time(17, 0, 0, tzinfo=UTC))
        self.assertEqual(root.cansched, True)
        self.assertEqual(root.domxferfee, Decimal("7.50"))
        self.assertEqual(root.intlxferfee, Decimal("17.50"))


class WirexfermsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSET")
        msgsetv1 = Wirexfermsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, WIREXFERMSGSET)
        self.assertIsInstance(root.wirexfermsgsetv1, WIREXFERMSGSETV1)


class Signonmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SIGNONMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
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
        root = Element("SIGNONMSGSET")
        signonmsgsetv1 = Signonmsgsetv1TestCase().root
        root.append(signonmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSET)
        self.assertIsInstance(root.signonmsgsetv1, SIGNONMSGSETV1)


class Signupmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE", "CHGUSERINFO", "AVAILACCTS", "CLIENTACTREQ"]

    @property
    def root(self):
        root = Element("SIGNUPMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        enroll = WebenrollTestCase().root
        root.append(enroll)
        SubElement(root, "CHGUSERINFO").text = "N"
        SubElement(root, "AVAILACCTS").text = "Y"
        SubElement(root, "CLIENTACTREQ").text = "N"
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

    requiredElements = ["SIGNUPMSGSETV1"]

    @property
    def root(self):
        root = Element("SIGNUPMSGSET")
        signup = Signupmsgsetv1TestCase().root
        root.append(signup)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SIGNUPMSGSET)
        self.assertIsInstance(instance.signupmsgsetv1, SIGNUPMSGSETV1)


class Profmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PROFMSGSRQV1")
        for i in range(2):
            proftrnrq = ProftrnrqTestCase().root
            root.append(proftrnrq)
        return root

    def testdataTags(self):
        # PROFMSGSRQV1 may only contain PROFTRNRQ
        allowedTags = PROFMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(ProftrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSRQV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, PROFTRNRQ)


class Profmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PROFMSGSRSV1")
        for i in range(2):
            proftrnrs = ProftrnrsTestCase().root
            root.append(proftrnrs)
        return root

    def testdataTags(self):
        # PROFMSGSRSV1 may only contain PROFTRNRS
        allowedTags = PROFMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(ProftrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, PROFTRNRS)


class Profmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE"]

    @property
    def root(self):
        root = Element("PROFMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
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
        root = Element("PROFMSGSET")
        msgsetv1 = Profmsgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PROFMSGSET)
        self.assertIsInstance(root.profmsgsetv1, PROFMSGSETV1)


class Invstmtmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "MSGSETCORE",
        "TRANDNLD",
        "OODNLD",
        "POSDNLD",
        "BALDNLD",
        "CANEMAIL",
    ]
    optionalElements = ["INV401KDNLD", "CLOSINGAVAIL"]

    @property
    def root(self):
        root = Element("INVSTMTMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "TRANDNLD").text = "Y"
        SubElement(root, "OODNLD").text = "Y"
        SubElement(root, "POSDNLD").text = "Y"
        SubElement(root, "BALDNLD").text = "Y"
        SubElement(root, "CANEMAIL").text = "N"
        SubElement(root, "INV401KDNLD").text = "N"
        SubElement(root, "CLOSINGAVAIL").text = "Y"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTMSGSETV1)
        self.assertIsInstance(instance.msgsetcore, MSGSETCORE)
        self.assertEqual(instance.trandnld, True)
        self.assertEqual(instance.oodnld, True)
        self.assertEqual(instance.posdnld, True)
        self.assertEqual(instance.baldnld, True)
        self.assertEqual(instance.canemail, False)
        self.assertEqual(instance.inv401kdnld, False)
        self.assertEqual(instance.closingavail, True)


class InvstmtmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INVSTMTMSGSET")
        invstmtmsgsetv1 = Invstmtmsgsetv1TestCase().root
        root.append(invstmtmsgsetv1)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTMSGSET)
        self.assertIsInstance(instance.invstmtmsgsetv1, INVSTMTMSGSETV1)


class Seclistmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SECLISTMSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "SECLISTRQDNLD").text = "N"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.seclistrqdnld, False)


class SeclistmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SECLISTMSGSET")
        seclistmsgsetv1 = Seclistmsgsetv1TestCase().root
        root.append(seclistmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSET)
        self.assertIsInstance(root.seclistmsgsetv1, SECLISTMSGSETV1)


class Tax1099msgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["MSGSETCORE", "TAX1099DNLD", "EXTD1099B", "TAXYEARSUPPORTED"]

    @property
    def root(self):
        root = Element("TAX1099MSGSETV1")
        msgsetcore = MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "TAX1099DNLD").text = "Y"
        SubElement(root, "EXTD1099B").text = "Y"
        SubElement(root, "TAXYEARSUPPORTED").text = "2005"
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
        root = Element("TAX1099MSGSET")
        msgsetv1 = Tax1099msgsetv1TestCase().root
        root.append(msgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, TAX1099MSGSET)
        self.assertIsInstance(root.tax1099msgsetv1, TAX1099MSGSETV1)


class MsgsetlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("MSGSETLIST")
        signon = SignonmsgsetTestCase().root
        root.append(signon)
        signup = SignupmsgsetTestCase().root
        root.append(signup)
        bankmsgset = ProfmsgsetTestCase().root
        root.append(bankmsgset)
        bankmsgset = BankmsgsetTestCase().root
        root.append(bankmsgset)
        creditcardmsgset = CreditcardmsgsetTestCase().root
        root.append(creditcardmsgset)
        invstmtmsgset = InvstmtmsgsetTestCase().root
        root.append(invstmtmsgset)
        seclistmsgset = SeclistmsgsetTestCase().root
        root.append(seclistmsgset)
        tax1099msgset = Tax1099msgsetTestCase().root
        root.append(tax1099msgset)
        return root

    def testdataTags(self):
        # MSGSETLIST may only contain
        # ["SIGNONMSGSET", "SIGNUPMSGSET", "PROFMSGSET", "BANKMSGSET",
        # "CREDITCARDMSGSET", "INTERXFERMSGSET", "WIREXFERMSGSET",
        # "INVSTMTMSGSET", "SECLISTMSGSET", "BILLPAYMSGSET", "PRESDIRMSGSET",
        # "PRESDLVMSGSET", "TAX1099MSGSET"]
        allowedTags = MSGSETLIST.dataTags
        self.assertEqual(len(allowedTags), 13)
        root = deepcopy(self.root)
        root.append(StmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        # Test MSGSETLIST wrapper.  *MSGSET members are tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MSGSETLIST)
        self.assertEqual(len(root), 8)
        self.assertIsInstance(root[0], SIGNONMSGSET)
        self.assertIsInstance(root[1], SIGNUPMSGSET)
        self.assertIsInstance(root[2], PROFMSGSET)
        self.assertIsInstance(root[3], BANKMSGSET)
        self.assertIsInstance(root[4], CREDITCARDMSGSET)
        self.assertIsInstance(root[5], INVSTMTMSGSET)
        self.assertIsInstance(root[6], SECLISTMSGSET)
        self.assertIsInstance(root[7], TAX1099MSGSET)


if __name__ == "__main__":
    unittest.main()
