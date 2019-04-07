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
    SIGNONINFO,
    SIGNONINFOLIST,
    MSGSETLIST,
)
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
from ofxtools.models.bank.xfer import INTRATRNRQ, INTRATRNRS
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
from ofxtools.models.i18n import LANG_CODES
from ofxtools.utils import UTC


# test imports
import base
from test_models_common import OfxextensionTestCase
from test_models_signup import WebenrollTestCase
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
from test_models_bank_xfer import IntratrnrqTestCase, IntratrnrsTestCase
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
    def msgsetlist(self):
        # Manually define MSGSETLIST here, to avoid circular import
        # from test_models_msgsets
        root = Element("MSGSETLIST")
        signonmsgset = Element("SIGNONMSGSET")
        signonmsgsetv1 = Element("SIGNONMSGSETV1")
        msgsetcore = Element("MSGSETCORE")
        SubElement(msgsetcore, "VER").text = "1"
        SubElement(msgsetcore, "URL").text = "https://ofxs.ameritrade.com/cgi-bin/apps/OFX"
        SubElement(msgsetcore, "OFXSEC").text = "NONE"
        SubElement(msgsetcore, "TRANSPSEC").text = "Y"
        SubElement(msgsetcore, "SIGNONREALM").text = "AMERITRADE"
        SubElement(msgsetcore, "LANGUAGE").text = "ENG"
        SubElement(msgsetcore, "SYNCMODE").text = "FULL"
        SubElement(msgsetcore, "REFRESHSUPT").text = "N"
        SubElement(msgsetcore, "RESPFILEER").text = "N"
        SubElement(msgsetcore, "INTU.TIMEOUT").text = "360"
        SubElement(msgsetcore, "SPNAME").text = "Dewey Cheatham & Howe"
        signonmsgsetv1.append(msgsetcore)
        signonmsgset.append(signonmsgsetv1)
        root.append(signonmsgset)

        return root

    @property
    def root(self):
        root = Element("PROFRS")
        msgsetlist = self.msgsetlist
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


class ProftrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = ProfrqTestCase


class ProftrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ProfrsTestCase

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        profile = instance.profile
        self.assertIsInstance(profile, PROFRS)


if __name__ == "__main__":
    unittest.main()
