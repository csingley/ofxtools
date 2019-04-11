# coding: utf-8
"""
Unit tests for models.msgsets
"""

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import time
from decimal import Decimal
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import OFXEXTENSION
from ofxtools.models import (
    MSGSETCORE,
    SIGNONMSGSRQV1, SIGNONMSGSRSV1, SIGNONMSGSETV1, SIGNONMSGSET,
    XFERPROF,
    STPCHKPROF,
    EMAILPROF,
    PROFMSGSRQV1, PROFMSGSRSV1, PROFMSGSETV1, PROFMSGSET,
    SIGNUPMSGSRQV1, SIGNUPMSGSRSV1, SIGNUPMSGSETV1, SIGNUPMSGSET,
    WEBENROLL,
    EMAILMSGSRQV1, EMAILMSGSRSV1, EMAILMSGSETV1, EMAILMSGSET,
    BANKMSGSRQV1, BANKMSGSRSV1, BANKMSGSETV1, BANKMSGSET,
    CREDITCARDMSGSRQV1, CREDITCARDMSGSRSV1, CREDITCARDMSGSETV1, CREDITCARDMSGSET,
    INTERXFERMSGSRQV1, INTERXFERMSGSRSV1, INTERXFERMSGSETV1, INTERXFERMSGSET,
    WIREXFERMSGSRQV1, WIREXFERMSGSRSV1, WIREXFERMSGSETV1, WIREXFERMSGSET,
    BILLPAYMSGSRQV1, BILLPAYMSGSRSV1, BILLPAYMSGSETV1, BILLPAYMSGSET,
    INVSTMTMSGSRQV1, INVSTMTMSGSRSV1, INVSTMTMSGSETV1, INVSTMTMSGSET,
    SECLISTMSGSRQV1, SECLISTMSGSRSV1, SECLISTMSGSETV1, SECLISTMSGSET,
    TAX1099MSGSETV1, TAX1099MSGSET,
)
from ofxtools.models.signon import SONRQ, SONRS
from ofxtools.models.profile import PROFTRNRQ, PROFTRNRS, MSGSETLIST
from ofxtools.models.signup import ENROLLTRNRQ, ENROLLTRNRS
from ofxtools.models.email import (
    MAILTRNRQ,
    MAILTRNRS,
    GETMIMETRNRQ,
    GETMIMETRNRS,
    MAILSYNCRQ,
    MAILSYNCRS,
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
#  from ofxtools.models.billpay import (
    #  PMTTRNRQ,
    #  RECPMTTRNRQ,
    #  PAYEETRNRQ,
    #  PMTINQTRNRQ,
    #  PMTMAILTRNRQ,
    #  PMTSYNCRQ,
    #  RECPMTSYNCRQ,
    #  PAYEESYNCRQ,
    #  PMTMAILSYNCRQ,
    #  PMTTRNRS,
    #  RECPMTTRNRS,
    #  PAYEETRNRS,
    #  PMTINQTRNRS,
    #  PMTMAILTRNRS,
    #  PMTSYNCRS,
    #  RECPMTSYNCRS,
    #  PAYEESYNCRS,
    #  PMTMAILSYNCRS,
#  )
from ofxtools.models.invest.stmt import INVSTMTTRNRQ, INVSTMTTRNRS
from ofxtools.models.invest import SECLIST
from ofxtools.models.i18n import LANG_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_common import OfxextensionTestCase
from test_models_signon import (
    SonrqTestCase,
    SonrsTestCase,
)
from test_models_profile import (
    ProftrnrqTestCase,
    ProftrnrsTestCase,
)
from test_models_email import (
    MailtrnrqTestCase,
    MailtrnrsTestCase,
    GetmimetrnrqTestCase,
    GetmimetrnrsTestCase,
    MailsyncrqTestCase,
    MailsyncrsTestCase,
)
from test_models_bank_stmt import (
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
    WiresyncrqTestCase,
    WiresyncrsTestCase,
    RecintrasyncrqTestCase,
    RecintrasyncrsTestCase,
    RecintersyncrqTestCase,
    RecintersyncrsTestCase,
    BankmailsyncrqTestCase,
    BankmailsyncrsTestCase,
)
#  from test_models_billpay_pmt import (
    #  PmttrnrqTestCase, PayeetrnrqTestCase, PmtinqtrnrqTestCase,
    #  PmttrnrsTestCase, PayeetrnrsTestCase, PmtinqtrnrsTestCase,
#  )
#  from test_models_billpay_recur import RecpmttrnrqTestCase, RecpmttrnrsTestCase
#  from test_models_billpay_mail import PmtmailtrnrqTestCase, PmtmailtrnrsTestCase
#  from test_models_billpay_sync import (
    #  PmtsyncRqTestCase,
    #  RecpmtsyncrqTestCase,
    #  PayeesyncrqTestCase,
    #  PmtmailsyncrqTestCase,
    #  PmtsyncRsTestCase,
    #  RecpmtsyncrsTestCase,
    #  PayeesyncrsTestCase,
    #  PmtmailsyncrsTestCase,
#  )
from test_models_invest import InvstmttrnrqTestCase, InvstmttrnrsTestCase
from test_models_securities import SeclisttrnrqTestCase, SeclisttrnrsTestCase, SeclistTestCase
from test_models_signup import WebenrollTestCase, EnrolltrnrqTestCase, EnrolltrnrsTestCase


class Signonmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SIGNONMSGSRQV1")
        sonrq = SonrqTestCase().root
        root.append(sonrq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSRQV1)
        self.assertIsInstance(root.sonrq, SONRQ)


class Signonmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SIGNONMSGSRSV1")
        sonrs = SonrsTestCase().root
        root.append(sonrs)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSRSV1)
        self.assertIsInstance(root.sonrs, SONRS)


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


class Profmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("PROFMSGSRQV1")
        for i in range(2):
            proftrnrq = ProftrnrqTestCase().root
            root.append(proftrnrq)
        return root

    def testListItem(self):
        # PROFMSGSRQV1 may only contain PROFTRNRQ
        listitems = PROFMSGSRQV1.listitems
        self.assertEqual(len(listitems), 1)
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

    def testListItems(self):
        # PROFMSGSRSV1 may only contain PROFTRNRS
        listitems = PROFMSGSRSV1.listitems
        self.assertEqual(len(listitems), 1)
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


class Signupmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SIGNUPMSGSRQV1")
        for i in range(2):
            enrolltrnrq = EnrolltrnrqTestCase().root
            root.append(enrolltrnrq)
        return root

    def testListItems(self):
        # SIGNUPMSGSRQV1 may contain
        # ["ENROLLTRNRQ", "ACCTINFOTRNRQ", "ACCTTRNRQ", "CHGUSERINFOTRNRQ"]
        listitems = SIGNUPMSGSRQV1.listitems
        self.assertEqual(len(listitems), 4)
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
        root = Element("SIGNUPMSGSRSV1")
        for i in range(2):
            enrolltrnrs = EnrolltrnrsTestCase().root
            root.append(enrolltrnrs)
        return root

    def testListItems(self):
        # SIGNUPMSGSRSV1 may contain
        # ["ENROLLTRNRS", "ACCTINFOTRNRS", "ACCTTRNRS", "CHGUSERINFOTRNRS"]
        listitems = SIGNUPMSGSRSV1.listitems
        self.assertEqual(len(listitems), 4)
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


class Emailmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILMSGSRQV1")
        for rq in (MailtrnrqTestCase, GetmimetrnrqTestCase, MailsyncrqTestCase):
            for i in range(2):
                root.append(rq().root)
        return root

    def testListItems(self):
        # EMAILMSGSRQV1 may contain ["MAILTRNRQ", "GETMIMETRNRQ", "MAILSYNCRQ"]

        listitems = EMAILMSGSRQV1.listitems
        self.assertEqual(len(listitems), 3)
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

    def testListItems(self):
        # EMAILMSGSRSV1 may contain ["MAILTRNRS", "GETMIMETRNRS", "MAILSYNCRS"]

        listitems = EMAILMSGSRSV1.listitems
        self.assertEqual(len(listitems), 3)
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

    def testListItems(self):
        # BANKMSGSRQV1 may contain
        # ["STMTTRNRQ", "STMTENDTRNRQ", "STPCHKTRNRQ", "INTRATRNRQ",
        # "RECINTRATRNRQ", "BANKMAILTRNRQ", "STPCHKSYNCRQ", "INTRASYNCRQ",
        # "RECINTRASYNCRQ", "BANKMAILSYNCRQ"]

        listitems = BANKMSGSRQV1.listitems
        self.assertEqual(len(listitems), 10)
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

    def testListItems(self):
        # BANKMSGSRSV! may contain
        # ["STMTTRNRS", "STMTENDRS", "STPCHKTRNRS", "INTRATRNRS",
        # "RECINTRATRNRS", "BANKMAILTRNRS", "STPCHKSYNCRS", "INTRASYNCRS",
        # "RECINTRASYNCRS", "BANKMAILSYNCRS"]
        listitems = BANKMSGSRSV1.listitems
        self.assertEqual(len(listitems), 10)
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
        SubElement(root, "DFLTDAYSTOPAY").text = "4"

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
        self.assertEqual(instance.dfltdaystopay, 4)


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

    def testListItems(self):
        # INTERXFERMSGSRQV1 may contain
        # ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]
        listitems = INTERXFERMSGSRQV1.listitems
        self.assertEqual(len(listitems), 4)
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

    def testListItems(self):
        # INTERXFERMSGSRSV1 may contain
        # ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]
        listitems = INTERXFERMSGSRSV1.listitems
        self.assertEqual(len(listitems), 4)
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



class Wirexfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRQV1")
        for rq in (WiretrnrqTestCase, WiresyncrqTestCase):
            for i in range(2):
                root.append(rq().root)
        return root

    def testListItems(self):
        # WIREXFERMSGSRQV1 may contain
        # ["WIRETRNRQ", "WIREERSYNCRQ"]
        listitems = WIREXFERMSGSRQV1.listitems
        self.assertEqual(len(listitems), 2)
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

    def testListItems(self):
        # WIRERXFERMSGSRSV1 may contain
        # ["WIRETRNRS", "WIRESYNCRS"]
        listitems = WIREXFERMSGSRSV1.listitems
        self.assertEqual(len(listitems), 2)
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


#  class Billpaymsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @property
    #  def root(self):
        #  root = Element("BILLPAYMSGSRQV1")
        #  for rq in (
            #  PmttrnrqTestCase, RecpmttrnrqTestCase, PayeetrnrqTestCase,
            #  PmtinqtrnrqTestCase, PmtmailtrnrqTestCase, PmtsyncRqTestCase,
            #  RecpmtsyncrqTestCase, PayeesyncrqTestCase, PmtmailsyncrqTestCase):
            #  for i in range(2):
                #  root.append(rq().root)
        #  return root

    #  def testListItems(self):
        #  # BILLPAYMSGSRQV1 may contain
        #  # [PMTTRNRQ, RECPMTTRNRQ, PAYEETRNRQ, PMTINQTRNRQ, PMTMAILTRNRQ,
        #  # PMTSYNCRQ, RECPMTSYNCRQ, PAYEESYNCRQ, PMTMAILSYNCRQ]
        #  listitems = BILLPAYMSGSRQV1.listitems
        #  self.assertEqual(len(listitems), 9)
        #  root = deepcopy(self.root)
        #  root.append(BillpaytrnrsTestCase().root)

        #  with self.assertRaises(ValueError):
            #  Aggregate.from_etree(root)

    #  def testConvert(self):
        #  instance = Aggregate.from_etree(self.root)
        #  self.assertIsInstance(instance, BILLPAYMSGSRQV1)
        #  self.assertEqual(len(instance), 4)
        #  self.assertIsInstance(instance[0], PMTTRNRQ)
        #  self.assertIsInstance(instance[1], PMTTRNRQ)
        #  self.assertIsInstance(instance[2], RECPMTTRNRQ)
        #  self.assertIsInstance(instance[3], RECPMTTRNRQ)
        #  self.assertIsInstance(instance[4], PAYEETRNRQ)
        #  self.assertIsInstance(instance[5], PAYEETRNRQ)
        #  self.assertIsInstance(instance[6], PMTINQTRNRQ)
        #  self.assertIsInstance(instance[7], PMTINQTRNRQ)
        #  self.assertIsInstance(instance[8], PMTMAILTRNRQ)
        #  self.assertIsInstance(instance[9], PMTMAILTRNRQ)
        #  self.assertIsInstance(instance[10], PMTSYNCRQ)
        #  self.assertIsInstance(instance[11], PMTSYNCRQ)
        #  self.assertIsInstance(instance[12], RECPMTSYNCRQ)
        #  self.assertIsInstance(instance[13], RECPMTSYNCRQ)
        #  self.assertIsInstance(instance[14], PAYEESYNCRQ)
        #  self.assertIsInstance(instance[15], PAYEESYNCRQ)
        #  self.assertIsInstance(instance[16], PMTMAILSYNCRQ)
        #  self.assertIsInstance(instance[17], PMTMAILSYNCRQ)


#  class Billpaymsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @property
    #  def root(self):
        #  root = Element("BILLPAYMSGSRSV1")
        #  for rq in (
            #  PmttrnrsTestCase, RecpmttrnrsTestCase, PayeetrnrsTestCase,
            #  PmtinqtrnrsTestCase, PmtmailtrnrsTestCase, PmtsyncRsTestCase,
            #  RecpmtsyncrsTestCase, PayeesyncrsTestCase, PmtmailsyncrsTestCase):
            #  for i in range(2):
                #  root.append(rq().root)
        #  return root

    #  def testListItems(self):
        #  # BILLPAYMSGSRQV1 may contain
        #  # [PMTTRNRS, RECPMTTRNRS, PAYEETRNRS, PMTINQTRNRS, PMTMAILTRNRS,
        #  # PMTSYNCRS, RECPMTSYNCRS, PAYEESYNCRS, PMTMAILSYNCRS]
        #  listitems = BILLPAYMSGSRSV1.listitems
        #  self.assertEqual(len(listitems), 9)
        #  root = deepcopy(self.root)
        #  root.append(BillpaytrnrsTestCase().root)

        #  with self.assertRaises(ValueError):
            #  Aggregate.from_etree(root)

    #  def testConvert(self):
        #  instance = Aggregate.from_etree(self.root)
        #  self.assertIsInstance(instance, BILLPAYMSGSRSV1)
        #  self.assertEqual(len(instance), 4)
        #  self.assertIsInstance(instance[0], PMTTRNRS)
        #  self.assertIsInstance(instance[1], PMTTRNRS)
        #  self.assertIsInstance(instance[2], RECPMTTRNRS)
        #  self.assertIsInstance(instance[3], RECPMTTRNRS)
        #  self.assertIsInstance(instance[4], PAYEETRNRS)
        #  self.assertIsInstance(instance[5], PAYEETRNRS)
        #  self.assertIsInstance(instance[6], PMTINQTRNRS)
        #  self.assertIsInstance(instance[7], PMTINQTRNRS)
        #  self.assertIsInstance(instance[8], PMTMAILTRNRS)
        #  self.assertIsInstance(instance[9], PMTMAILTRNRS)
        #  self.assertIsInstance(instance[10], PMTSYNCRS)
        #  self.assertIsInstance(instance[11], PMTSYNCRS)
        #  self.assertIsInstance(instance[12], RECPMTSYNCRS)
        #  self.assertIsInstance(instance[13], RECPMTSYNCRS)
        #  self.assertIsInstance(instance[14], PAYEESYNCRS)
        #  self.assertIsInstance(instance[15], PAYEESYNCRS)
        #  self.assertIsInstance(instance[16], PMTMAILSYNCRS)
        #  self.assertIsInstance(instance[17], PMTMAILSYNCRS)


#  class Billpaymsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @property
    #  def root(self):
        #  root = Element("BILLPAYMSGSETV1")
        #  msgsetcore = MsgsetcoreTestCase().root
        #  root.append(msgsetcore)
        #  SubElement(root, "DAYSWITH").text = "2"
        #  SubElement(root, "DFLTDAYSTOPAY").text = "4"
        #  SubElement(root, "XFERDAYSWITH").text = "3"
        #  SubElement(root, "XFERDFLTDAYSTOPAY").text = "5"
        #  SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        #  SubElement(root, "PROCENDTM").text = "170000"
        #  SubElement(root, "MODELWND").text = "3"
        #  SubElement(root, "POSTPROCWND").text = "6"
        #  SubElement(root, "STSVIAMODS").text = "N"
        #  SubElement(root, "PMTBYADDR").text = "Y"
        #  SubElement(root, "PMTBYXFER").text = "Y"
        #  SubElement(root, "PMTBYPAYEEID").text = "N"
        #  SubElement(root, "CANADDPAYEE").text = "Y"
        #  SubElement(root, "HASEXTDPMT").text = "N"
        #  SubElement(root, "CANMODPMTS").text = "N"
        #  SubElement(root, "CANMODMDLS").text = "Y"
        #  SubElement(root, "DIFFFIRSTPMT").text = "N"
        #  SubElement(root, "DIFFLASTPMT").text = "N"
        #  SubElement(root, "BILLPUBCONTEXT").text = "Y"

        #  return root

    #  def testConvert(self):
        #  root = Aggregate.from_etree(self.root)
        #  self.assertIsInstance(root, BILLPAYMSGSETV1)
        #  self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        #  self.assertEqual(root.dayswith, 2)
        #  self.assertEqual(root.dfltdaystopay, 4)
        #  self.assertEqual(root.xferdayswith, 3)
        #  self.assertEqual(root.xferdfltdaystopay, 5)
        #  self.assertIsNone(root.procdaysoff)  # Unsupported
        #  self.assertEqual(root.procendtm, time(17, 0, 0, tzinfo=UTC))
        #  self.assertEqual(root.modelwnd, 3)
        #  self.assertEqual(root.postprocwnd, 6)
        #  self.assertEqual(root.stsviamods, False)
        #  self.assertEqual(root.pmtbyaddr, True)
        #  self.assertEqual(root.pmtbyxfer, True)
        #  self.assertEqual(root.pmtbypayeeid, False)
        #  self.assertEqual(root.canaddpayee, True)
        #  self.assertEqual(root.hasextdpmt, False)
        #  self.assertEqual(root.canmodpmts, False)
        #  self.assertEqual(root.canmodmdls, True)
        #  self.assertEqual(root.difffirstpmt, False)
        #  self.assertEqual(root.difflastpmt, False)
        #  self.assertEqual(root.billpubcontent, True)

        #  self.assertEqual(root.cansched, True)
        #  self.assertEqual(root.domxferfee, Decimal("7.50"))
        #  self.assertEqual(root.intlxferfee, Decimal("17.50"))



#  class BillpaymsgsetTestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @property
    #  def root(self):
        #  root = Element("WIREXFERMSGSET")
        #  msgsetv1 = Billpaymsgsetv1TestCase().root
        #  root.append(msgsetv1)
        #  return root

    #  def testConvert(self):
        #  root = Aggregate.from_etree(self.root)
        #  self.assertIsInstance(root, BILLPAYMSGSET)
        #  self.assertIsInstance(root.billpaymsgsetv1, BILLPAYMSGSETV1)


class Invstmtmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INVSTMTMSGSRQV1")
        for i in range(2):
            stmttrnrq = InvstmttrnrqTestCase().root
            root.append(stmttrnrq)
        return root

    def testListItems(self):
        # INVSTMTMSGSRQV1 may only contain
        # ["INVSTMTTRNRQ", "INVMAILTRNRQ", "INVMAILSYNCRQ"]
        listitems = INVSTMTMSGSRQV1.listitems
        self.assertEqual(len(listitems), 3)
        root = deepcopy(self.root)
        root.append(InvstmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTMSGSRQV1)
        self.assertEqual(len(instance), 2)
        for stmttrnrs in instance:
            self.assertIsInstance(stmttrnrs, INVSTMTTRNRQ)


class Invstmtmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INVSTMTMSGSRSV1")
        for i in range(2):
            stmttrnrs = InvstmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testListItems(self):
        # INVSTMTMSGSRSV1 may only contain
        # ["INVSTMTTRNRS", "INVMAILTRNRS", "INVMAILSYNCRS"]
        listitems = INVSTMTMSGSRSV1.listitems
        self.assertEqual(len(listitems), 3)
        root = deepcopy(self.root)
        root.append(InvstmttrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INVSTMTMSGSRSV1)
        self.assertEqual(len(instance), 2)
        for stmttrnrs in instance:
            self.assertIsInstance(stmttrnrs, INVSTMTTRNRS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIs(instance.statements[0], instance[0].invstmtrs)


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


class Seclistmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("SECLISTMSGSRQV1")
        for i in range(2):
            root.append(SeclisttrnrqTestCase().root)
        return root

    def testListItems(self):
        # SECLISTMSGSRQV1 may only contain SECLISTTRNRQ

        listitems = SECLISTMSGSRQV1.listitems
        self.assertEqual(len(listitems), 1)
        root = deepcopy(self.root)
        root.append(SeclisttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, SECLISTMSGSRQV1)
        self.assertEqual(len(instance), 2)


class Seclistmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    # FIXME
    # requiredElements = ('SECLIST',)

    @property
    def root(self):
        root = Element("SECLISTMSGSRSV1")
        seclist = SeclistTestCase().root
        root.append(seclist)
        root.append(deepcopy(seclist))
        return root

    def testListItems(self):
        # SECLISTMSGSRSV1 may only contain SECLISTTRNRS, SECLIST

        listitems = SECLISTMSGSRSV1.listitems
        self.assertEqual(len(listitems), 2)
        root = deepcopy(self.root)
        root.append(SeclisttrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSRSV1)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], SECLIST)
        self.assertIsInstance(root[1], SECLIST)


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


#  Test models.profile.MSGSETLIST here to avoid circular imports
class MsgsetlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def validSoup(cls):
        msgsets = [
            SignonmsgsetTestCase().root,
            SignupmsgsetTestCase().root,
            ProfmsgsetTestCase().root,
            BankmsgsetTestCase().root,
            CreditcardmsgsetTestCase().root,
            InterxfermsgsetTestCase().root,
            WirexfermsgsetTestCase().root,
            InvstmtmsgsetTestCase().root,
            SeclistmsgsetTestCase().root,
            #  BillpaymsgsetTestCase().root,
            Tax1099msgsetTestCase().root,
        ]
        root = Element("MSGSETLIST")
        for msgset in msgsets:
            root.append(msgset)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Empty MSGSETLIST
        root = Element("MSGSETLIST")
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    def testListItems(self):
        # MSGSETLIST may only contain
        # ["SIGNONMSGSET", "SIGNUPMSGSET", "PROFMSGSET", "BANKMSGSET",
        # "CREDITCARDMSGSET", "INTERXFERMSGSET", "WIREXFERMSGSET",
        # "INVSTMTMSGSET", "SECLISTMSGSET", "BILLPAYMSGSET", "PRESDIRMSGSET",
        # "PRESDLVMSGSET", "TAX1099MSGSET"]
        listitems = MSGSETLIST.listitems
        #  self.assertEqual(len(listitems), 13)
        self.assertEqual(len(listitems), 11)
        root = deepcopy(self.root)
        root.append(StmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


if __name__ == "__main__":
    unittest.main()
