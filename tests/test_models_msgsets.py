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

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONMSGSRQV1")
        root.append(SonrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONMSGSRQV1(sonrq=SonrqTestCase.aggregate)


class Signonmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONMSGSRSV1")
        root.append(SonrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONMSGSRSV1(sonrs=SonrsTestCase.aggregate)


class Signonmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate)


class SignonmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONMSGSET")
        root.append(Signonmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONMSGSET(signonmsgsetv1=Signonmsgsetv1TestCase.aggregate)


class Profmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFMSGSRQV1")
        for i in range(2):
            root.append(ProftrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFMSGSRQV1(ProftrnrqTestCase.aggregate,
                            ProftrnrqTestCase.aggregate)

    def testListItem(self):
        # PROFMSGSRQV1 may only contain PROFTRNRQ
        listitems = PROFMSGSRQV1.listitems
        self.assertEqual(len(listitems), 1)
        root = self.etree
        root.append(ProftrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Profmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFMSGSRSV1")
        for i in range(2):
            root.append(ProftrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFMSGSRSV1(ProftrnrsTestCase.aggregate, ProftrnrsTestCase.aggregate)

    def testListItems(self):
        # PROFMSGSRSV1 may only contain PROFTRNRS
        listitems = PROFMSGSRSV1.listitems
        self.assertEqual(len(listitems), 1)
        root = self.etree
        root.append(ProftrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Profmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate)


class ProfmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFMSGSET")
        root.append(Profmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFMSGSET(profmsgsetv1=Profmsgsetv1TestCase.aggregate)


class Signupmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNUPMSGSRQV1")
        for i in range(2):
            root.append(EnrolltrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSRQV1(EnrolltrnrqTestCase.aggregate,
                              EnrolltrnrqTestCase.aggregate)

    def testListItems(self):
        # SIGNUPMSGSRQV1 may contain
        # ["ENROLLTRNRQ", "ACCTINFOTRNRQ", "ACCTTRNRQ", "CHGUSERINFOTRNRQ"]
        listitems = SIGNUPMSGSRQV1.listitems
        self.assertEqual(len(listitems), 4)
        root = self.etree
        root.append(EnrolltrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Signupmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNUPMSGSRSV1")
        for i in range(2):
            root.append(EnrolltrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSRSV1(EnrolltrnrsTestCase.aggregate, EnrolltrnrsTestCase.aggregate)

    def testListItems(self):
        # SIGNUPMSGSRSV1 may contain
        # ["ENROLLTRNRS", "ACCTINFOTRNRS", "ACCTTRNRS", "CHGUSERINFOTRNRS"]
        listitems = SIGNUPMSGSRSV1.listitems
        self.assertEqual(len(listitems), 4)
        root = self.etree
        root.append(EnrolltrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Signupmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE", "CHGUSERINFO", "AVAILACCTS", "CLIENTACTREQ"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNUPMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        root.append(WebenrollTestCase.etree)
        SubElement(root, "CHGUSERINFO").text = "N"
        SubElement(root, "AVAILACCTS").text = "Y"
        SubElement(root, "CLIENTACTREQ").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                              webenroll=WebenrollTestCase.aggregate,
                              chguserinfo=False,
                              availaccts=True,
                              clientactreq=False)


class SignupmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SIGNUPMSGSETV1"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNUPMSGSET")
        root.append(Signupmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSET(signupmsgsetv1=Signupmsgsetv1TestCase.aggregate)


class Emailmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EMAILMSGSRQV1")
        for rq in (MailtrnrqTestCase, GetmimetrnrqTestCase, MailsyncrqTestCase):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILMSGSRQV1(
            MailtrnrqTestCase.aggregate, MailtrnrqTestCase.aggregate,
            GetmimetrnrqTestCase.aggregate, GetmimetrnrqTestCase.aggregate,
            MailsyncrqTestCase.aggregate, MailsyncrqTestCase.aggregate)

    def testListItems(self):
        # EMAILMSGSRQV1 may contain ["MAILTRNRQ", "GETMIMETRNRQ", "MAILSYNCRQ"]
        listitems = EMAILMSGSRQV1.listitems
        self.assertEqual(len(listitems), 3)
        root = self.etree
        root.append(MailtrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Emailmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EMAILMSGSRSV1")
        for rs in (MailtrnrsTestCase, GetmimetrnrsTestCase, MailsyncrsTestCase):
            for i in range(2):
                root.append(rs.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILMSGSRSV1(MailtrnrsTestCase.aggregate,
                             MailtrnrsTestCase.aggregate,
                             GetmimetrnrsTestCase.aggregate,
                             GetmimetrnrsTestCase.aggregate,
                             
                             MailsyncrsTestCase.aggregate, MailsyncrsTestCase.aggregate)

    def testListItems(self):
        # EMAILMSGSRSV1 may contain ["MAILTRNRS", "GETMIMETRNRS", "MAILSYNCRS"]
        listitems = EMAILMSGSRSV1.listitems
        self.assertEqual(len(listitems), 3)
        root = self.etree
        root.append(MailtrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Emailmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EMAILMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "MAILSUP").text = "Y"
        SubElement(root, "GETMIMESUP").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                             mailsup=True, getmimesup=True)


class EmailmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EMAILMSGSET")
        root.append(Emailmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILMSGSET(emailmsgsetv1=Emailmsgsetv1TestCase.aggregate)


class Bankmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
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
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSRQV1(StmttrnrqTestCase.aggregate,
                            StmttrnrqTestCase.aggregate,
                            StmtendtrnrqTestCase.aggregate,
                            StmtendtrnrqTestCase.aggregate,
                            StpchktrnrqTestCase.aggregate,
                            StpchktrnrqTestCase.aggregate,
                            IntratrnrqTestCase.aggregate,
                            IntratrnrqTestCase.aggregate,
                            RecintratrnrqTestCase.aggregate,
                            RecintratrnrqTestCase.aggregate,
                            BankmailtrnrqTestCase.aggregate,
                            BankmailtrnrqTestCase.aggregate,
                            StpchksyncrqTestCase.aggregate,
                            StpchksyncrqTestCase.aggregate,
                            IntrasyncrqTestCase.aggregate,
                            IntrasyncrqTestCase.aggregate,
                            RecintrasyncrqTestCase.aggregate,
                            RecintrasyncrqTestCase.aggregate,
                            BankmailsyncrqTestCase.aggregate,
                            BankmailsyncrqTestCase.aggregate)

    def testListItems(self):
        # BANKMSGSRQV1 may contain
        # ["STMTTRNRQ", "STMTENDTRNRQ", "STPCHKTRNRQ", "INTRATRNRQ",
        # "RECINTRATRNRQ", "BANKMAILTRNRQ", "STPCHKSYNCRQ", "INTRASYNCRQ",
        # "RECINTRASYNCRQ", "BANKMAILSYNCRQ"]

        listitems = BANKMSGSRQV1.listitems
        self.assertEqual(len(listitems), 10)
        root = self.etree
        root.append(StmttrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Bankmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
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
                root.append(rs.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSRSV1(StmttrnrsTestCase.aggregate,
                            StmttrnrsTestCase.aggregate,
                            StmtendtrnrsTestCase.aggregate,
                            StmtendtrnrsTestCase.aggregate,
                            StpchktrnrsTestCase.aggregate,
                            StpchktrnrsTestCase.aggregate,
                            IntratrnrsTestCase.aggregate,
                            IntratrnrsTestCase.aggregate,
                            RecintratrnrsTestCase.aggregate,
                            RecintratrnrsTestCase.aggregate,
                            BankmailtrnrsTestCase.aggregate,
                            BankmailtrnrsTestCase.aggregate,
                            StpchksyncrsTestCase.aggregate,
                            StpchksyncrsTestCase.aggregate,
                            IntrasyncrsTestCase.aggregate,
                            IntrasyncrsTestCase.aggregate,
                            RecintrasyncrsTestCase.aggregate,
                            RecintrasyncrsTestCase.aggregate,
                            BankmailsyncrsTestCase.aggregate,
                            BankmailsyncrsTestCase.aggregate)

    def testListItems(self):
        # BANKMSGSRSV! may contain
        # ["STMTTRNRS", "STMTENDRS", "STPCHKTRNRS", "INTRATRNRS",
        # "RECINTRATRNRS", "BANKMAILTRNRS", "STPCHKSYNCRS", "INTRASYNCRS",
        # "RECINTRASYNCRS", "BANKMAILSYNCRS"]
        listitems = BANKMSGSRSV1.listitems
        self.assertEqual(len(listitems), 10)
        root = self.etree
        root.append(StmttrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertIsInstance(instance.statements, list)
        self.assertEqual(len(instance.statements), 2)
        self.assertIsInstance(instance.statements[0], STMTRS)
        self.assertIsInstance(instance.statements[1], STMTRS)


class XferprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("XFERPROF")
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000.000[0:GMT]"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "CANRECUR").text = "Y"
        SubElement(root, "CANMODXFER").text = "N"
        SubElement(root, "CANMODMDLS").text = "Y"
        SubElement(root, "MODELWND").text = "3"
        SubElement(root, "DAYSWITH").text = "2"
        SubElement(root, "DFLTDAYSTOPAY").text = "4"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return XFERPROF("SUNDAY",
                        procendtm=time(17, 0, 0, tzinfo=UTC), cansched=True,
                        canrecur=True, canmodxfer=False, canmodmdls=True,
                        modelwnd=3, dayswith=2, dfltdaystopay=4)


class StpchkprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STPCHKPROF")
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000.000[0:GMT]"
        SubElement(root, "CANUSERANGE").text = "Y"
        SubElement(root, "CANUSEDESC").text = "Y"
        SubElement(root, "STPCHKFEE").text = "30.1"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKPROF("SUNDAY",
                          procendtm=time(17, 0, 0, tzinfo=UTC),
                          canuserange=True, canusedesc=True,
                          stpchkfee=Decimal("30.1"))


class EmailprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EMAILPROF")
        SubElement(root, "CANEMAIL").text = "Y"
        SubElement(root, "CANNOTIFY").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILPROF(canemail=True, cannotify=False)


class Bankmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    oneOfs = {"INVALIDACCTTYPE": ACCTTYPES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "INVALIDACCTTYPE").text = "CHECKING"
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        SubElement(root, "PENDINGAVAIL").text = "N"
        root.append(XferprofTestCase.etree)
        root.append(StpchkprofTestCase.etree)
        root.append(EmailprofTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                            invalidaccttype="CHECKING",
                            closingavail=True, pendingavail=False,
                            xferprof=XferprofTestCase.aggregate,
                            stpchkprof=StpchkprofTestCase.aggregate,
                            emailprof=EmailprofTestCase.aggregate)


class BankmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKMSGSET")
        root.append(Bankmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSET(bankmsgsetv1=Bankmsgsetv1TestCase.aggregate)


class Creditcardmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CREDITCARDMSGSRQV1")
        root.append(CcstmttrnrqTestCase.etree)
        root.append(CcstmtendtrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CREDITCARDMSGSRQV1(CcstmttrnrqTestCase.aggregate,
                                  CcstmtendtrnrqTestCase.aggregate)


class Creditcardmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CREDITCARDMSGSRSV1")
        root.append(CcstmttrnrsTestCase.etree)
        root.append(CcstmtendtrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CREDITCARDMSGSRSV1(CcstmttrnrsTestCase.aggregate,
                                  CcstmtendtrnrsTestCase.aggregate)


class Creditcardmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE", "CLOSINGAVAIL"]
    optionalElements = ["PENDINGAVAIL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CREDITCARDMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        SubElement(root, "PENDINGAVAIL").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CREDITCARDMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                                  closingavail=True, pendingavail=False)


class CreditcardmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CREDITCARDMSGSET")
        root.append(Creditcardmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CREDITCARDMSGSET(creditcardmsgsetv1=Creditcardmsgsetv1TestCase.aggregate)


class Interxfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERXFERMSGSRQV1")
        for rq in (
            IntertrnrqTestCase,
            RecintertrnrqTestCase,
            IntersyncrqTestCase,
            RecintersyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERXFERMSGSRQV1(IntertrnrqTestCase.aggregate,
                                 IntertrnrqTestCase.aggregate,
                                 RecintertrnrqTestCase.aggregate,
                                 RecintertrnrqTestCase.aggregate,
                                 IntersyncrqTestCase.aggregate,
                                 IntersyncrqTestCase.aggregate,
                                 RecintersyncrqTestCase.aggregate,
                                 RecintersyncrqTestCase.aggregate)

    def testListItems(self):
        # INTERXFERMSGSRQV1 may contain
        # ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]
        listitems = INTERXFERMSGSRQV1.listitems
        self.assertEqual(len(listitems), 4)
        root = self.etree
        root.append(IntertrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Interxfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERXFERMSGSRSV1")
        for rq in (
            IntertrnrsTestCase,
            RecintertrnrsTestCase,
            IntersyncrsTestCase,
            RecintersyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERXFERMSGSRSV1(IntertrnrsTestCase.aggregate,
                                 IntertrnrsTestCase.aggregate,
                                 RecintertrnrsTestCase.aggregate,
                                 RecintertrnrsTestCase.aggregate,
                                 IntersyncrsTestCase.aggregate,
                                 IntersyncrsTestCase.aggregate,
                                 RecintersyncrsTestCase.aggregate,
                                 RecintersyncrsTestCase.aggregate)

    def testListItems(self):
        # INTERXFERMSGSRSV1 may contain
        # ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]
        listitems = INTERXFERMSGSRSV1.listitems
        self.assertEqual(len(listitems), 4)
        root = self.etree
        root.append(IntertrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Interxfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERXFERMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        root.append(XferprofTestCase.etree)
        SubElement(root, "CANBILLPAY").text = "Y"
        SubElement(root, "CANCWND").text = "2"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERXFERMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                                 xferprof=XferprofTestCase.aggregate,
                                 canbillpay=True, cancwnd=2,
                                 domxferfee=Decimal("7.50"),
                                 intlxferfee=Decimal("17.50"))


class InterxfermsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERXFERMSGSET")
        root.append(Interxfermsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERXFERMSGSET(interxfermsgsetv1=Interxfermsgsetv1TestCase.aggregate)


class Wirexfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREXFERMSGSRQV1")
        for rq in (WiretrnrqTestCase, WiresyncrqTestCase):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSRQV1(WiretrnrqTestCase.aggregate,
                                WiretrnrqTestCase.aggregate,
                                WiresyncrqTestCase.aggregate,
                                WiresyncrqTestCase.aggregate)

    def testListItems(self):
        # WIREXFERMSGSRQV1 may contain
        # ["WIRETRNRQ", "WIREERSYNCRQ"]
        listitems = WIREXFERMSGSRQV1.listitems
        self.assertEqual(len(listitems), 2)
        root = self.etree
        root.append(WiretrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Wirexfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREXFERMSGSRSV1")
        for rq in (WiretrnrsTestCase, WiresyncrsTestCase):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSRSV1(WiretrnrsTestCase.aggregate,
                                WiretrnrsTestCase.aggregate,
                                WiresyncrsTestCase.aggregate,
                                WiresyncrsTestCase.aggregate)

    def testListItems(self):
        # WIRERXFERMSGSRSV1 may contain
        # ["WIRETRNRS", "WIRESYNCRS"]
        listitems = WIREXFERMSGSRSV1.listitems
        self.assertEqual(len(listitems), 2)
        root = self.etree
        root.append(WiretrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Wirexfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREXFERMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000.000[0:GMT]"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSETV1("SUNDAY",
                                msgsetcore=MsgsetcoreTestCase.aggregate,
                                procendtm=time(17, 0, 0, tzinfo=UTC),
                                cansched=True,
                                domxferfee=Decimal("7.50"),
                                intlxferfee=Decimal("17.50"))


class WirexfermsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREXFERMSGSET")
        root.append(Wirexfermsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSET(wirexfermsgsetv1=Wirexfermsgsetv1TestCase.aggregate)


#  class Billpaymsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @classproperty
    #  @classmethod
    #  def etree(cls):
        #  root = Element("BILLPAYMSGSRQV1")
        #  for rq in (
            #  PmttrnrqTestCase, RecpmttrnrqTestCase, PayeetrnrqTestCase,
            #  PmtinqtrnrqTestCase, PmtmailtrnrqTestCase, PmtsyncRqTestCase,
            #  RecpmtsyncrqTestCase, PayeesyncrqTestCase, PmtmailsyncrqTestCase):
            #  for i in range(2):
                #  root.append(rq.etree)
        #  return root

    #  @classproperty
    #  @classmethod
    #  def aggregate(cls):
        #  return BILLPAYMSGSRQV1(PmttrnrqTestCase.aggregate,
                               #  PmttrnrqTestCase.aggregate,
                               #  RecpmttrnrqTestCase.aggregate,
                               #  RecpmttrnrqTestCase.aggregate,
                               #  PayeetrnrqTestCase.aggregate,
                               #  PayeetrnrqTestCase.aggregate,
                               #  PmtinqtrnrqTestCase.aggregate,
                               #  PmtinqtrnrqTestCase.aggregate,
                               #  PmtmailtrnrqTestCase.aggregate,
                               #  PmtmailtrnrqTestCase.aggregate,
                               #  PmtsyncrqTestCase.aggregate,
                               #  PmtsyncrqTestCase.aggregate,
                               #  RecpmtsyncrqTestCase.aggregate,
                               #  RecpmtsyncrqTestCase.aggregate,
                               #  PayeesyncrqTestCase.aggregate,
                               #  PayeesyncrqTestCase.aggregate,
                               #  PmtmailsyncrqTestCase.aggregate,
                               #  PmtmailsyncrqTestCase.aggregate)

    #  def testListItems(self):
        #  # BILLPAYMSGSRQV1 may contain
        #  # [PMTTRNRQ, RECPMTTRNRQ, PAYEETRNRQ, PMTINQTRNRQ, PMTMAILTRNRQ,
        #  # PMTSYNCRQ, RECPMTSYNCRQ, PAYEESYNCRQ, PMTMAILSYNCRQ]
        #  listitems = BILLPAYMSGSRQV1.listitems
        #  self.assertEqual(len(listitems), 9)
        #  root = self.etree
        #  root.append(BillpaytrnrsTestCase.etree)

        #  with self.assertRaises(ValueError):
            #  Aggregate.from_etree(root)


#  class Billpaymsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @classproperty
    #  @classmethod
    #  def etree(cls):
        #  root = Element("BILLPAYMSGSRSV1")
        #  for rq in (
            #  PmttrnrsTestCase, RecpmttrnrsTestCase, PayeetrnrsTestCase,
            #  PmtinqtrnrsTestCase, PmtmailtrnrsTestCase, PmtsyncRsTestCase,
            #  RecpmtsyncrsTestCase, PayeesyncrsTestCase, PmtmailsyncrsTestCase):
            #  for i in range(2):
                #  root.append(rq.etree)
        #  return root

    #  @classproperty
    #  @classmethod
    #  def aggregate(cls):
        #  return BILLPAYMSGSRSV1(PmttrnrsTestCase.aggregate,
                               #  PmttrnrsTestCase.aggregate,
                               #  RecpmttrnrsTestCase.aggregate,
                               #  RecpmttrnrsTestCase.aggregate,
                               #  PayeetrnrsTestCase.aggregate,
                               #  PayeetrnrsTestCase.aggregate,
                               #  PmtinqtrnrsTestCase.aggregate,
                               #  PmtinqtrnrsTestCase.aggregate,
                               #  PmtmailtrnrsTestCase.aggregate,
                               #  PmtmailtrnrsTestCase.aggregate,
                               #  PmtsyncrsTestCase.aggregate,
                               #  PmtsyncrsTestCase.aggregate,
                               #  RecpmtsyncrsTestCase.aggregate,
                               #  RecpmtsyncrsTestCase.aggregate,
                               #  PayeesyncrsTestCase.aggregate,
                               #  PayeesyncrsTestCase.aggregate,
                               #  PmtmailsyncrsTestCase.aggregate,
                               #  PmtmailsyncrsTestCase.aggregate)

    #  def testListItems(self):
        #  # BILLPAYMSGSRQV1 may contain
        #  # [PMTTRNRS, RECPMTTRNRS, PAYEETRNRS, PMTINQTRNRS, PMTMAILTRNRS,
        #  # PMTSYNCRS, RECPMTSYNCRS, PAYEESYNCRS, PMTMAILSYNCRS]
        #  listitems = BILLPAYMSGSRSV1.listitems
        #  self.assertEqual(len(listitems), 9)
        #  root = self.etree
        #  root.append(BillpaytrnrsTestCase.etree)

        #  with self.assertRaises(ValueError):
            #  Aggregate.from_etree(root)


#  class Billpaymsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @classproperty
    #  @classmethod
    #  def etree(cls):
        #  root = Element("BILLPAYMSGSETV1")
        #  root.append(MsgsetcoreTestCase.etree)
        #  SubElement(root, "DAYSWITH").text = "2"
        #  SubElement(root, "DFLTDAYSTOPAY").text = "4"
        #  SubElement(root, "XFERDAYSWITH").text = "3"
        #  SubElement(root, "XFERDFLTDAYSTOPAY").text = "5"
        #  SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        #  SubElement(root, "PROCENDTM").text = "170000.000[0:GMT]"
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

    #  @classproperty
    #  @classmethod
    #  def aggregate(cls):
        #  return BILLPAYMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                               #  dayswith=2, dfltdaystopay=4, xferdayswith=3,
                               #  xferdfltdaystopay=5, procdaysoff=None,  # Unsupported
                               #  procendtm=time(17, 0, 0, tzinfo=UTC),
                               #  modelwnd=3, postprocwnd=6, stsviamods=False,
                               #  pmtbyaddr=True, pmtbyxfer=True,
                               #  pmtbypayeeid=False, canaddpayee=True,
                               #  hasextdpmt=False, canmodpmts=False,
                               #  canmodmdls=True, difffirstpmt=False,
                               #  difflastpmt=False, billpubcontent=True,
                               #  cansched=True, domxferfee=Decimal("7.50"),
                               #  intlxferfee=Decimal("17.50"))


#  class BillpaymsgsetTestCase(unittest.TestCase, base.TestAggregate):
    #  __test__ = True

    #  @classproperty
    #  @classmethod
    #  def etree(cls):
        #  root = Element("WIREXFERMSGSET")
        #  root.append(Billpaymsgsetv1TestCase.etree)
        #  return root

    #  @classproperty
    #  @classmethod
    #  def aggregate(cls):
        #  return BILLPAYMSGSET(billpaymsgsetv1=Billpaymsgsetv1TestCase.aggregate)


class Invstmtmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTMSGSRQV1")
        for i in range(2):
            stmttrnrq = InvstmttrnrqTestCase.etree
            root.append(stmttrnrq)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTMSGSRQV1(InvstmttrnrqTestCase.aggregate,
                               InvstmttrnrqTestCase.aggregate)

    def testListItems(self):
        # INVSTMTMSGSRQV1 may only contain
        # ["INVSTMTTRNRQ", "INVMAILTRNRQ", "INVMAILSYNCRQ"]
        listitems = INVSTMTMSGSRQV1.listitems
        self.assertEqual(len(listitems), 3)
        root = self.etree
        root.append(InvstmttrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Invstmtmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTMSGSRSV1")
        for i in range(2):
            stmttrnrs = InvstmttrnrsTestCase.etree
            root.append(stmttrnrs)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTMSGSRSV1(InvstmttrnrsTestCase.aggregate, InvstmttrnrsTestCase.aggregate)

    def testListItems(self):
        # INVSTMTMSGSRSV1 may only contain
        # ["INVSTMTTRNRS", "INVMAILTRNRS", "INVMAILSYNCRS"]
        listitems = INVSTMTMSGSRSV1.listitems
        self.assertEqual(len(listitems), 3)
        root = self.etree
        root.append(InvstmttrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
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

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "TRANDNLD").text = "Y"
        SubElement(root, "OODNLD").text = "Y"
        SubElement(root, "POSDNLD").text = "Y"
        SubElement(root, "BALDNLD").text = "Y"
        SubElement(root, "CANEMAIL").text = "N"
        SubElement(root, "INV401KDNLD").text = "N"
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                               trandnld=True, oodnld=True, posdnld=True,
                               baldnld=True, canemail=False, inv401kdnld=False,
                               closingavail=True)


class InvstmtmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTMSGSET")
        root.append(Invstmtmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTMSGSET(invstmtmsgsetv1=Invstmtmsgsetv1TestCase.aggregate)


class Seclistmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLISTMSGSRQV1")
        for i in range(2):
            root.append(SeclisttrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTMSGSRQV1(SeclisttrnrqTestCase.aggregate,
                               SeclisttrnrqTestCase.aggregate)

    def testListItems(self):
        # SECLISTMSGSRQV1 may only contain SECLISTTRNRQ

        listitems = SECLISTMSGSRQV1.listitems
        self.assertEqual(len(listitems), 1)
        root = self.etree
        root.append(SeclisttrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Seclistmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    # FIXME
    # requiredElements = ('SECLIST',)

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLISTMSGSRSV1")
        root.append(SeclistTestCase.etree)
        root.append(SeclistTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTMSGSRSV1(SeclistTestCase.aggregate,
                               SeclistTestCase.aggregate)

    def testListItems(self):
        # SECLISTMSGSRSV1 may only contain SECLISTTRNRS, SECLIST

        listitems = SECLISTMSGSRSV1.listitems
        self.assertEqual(len(listitems), 2)
        root = self.etree
        root.append(SeclisttrnrqTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class Seclistmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLISTMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "SECLISTRQDNLD").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTMSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                               seclistrqdnld=False)


class SeclistmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLISTMSGSET")
        root.append(Seclistmsgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTMSGSET(seclistmsgsetv1=Seclistmsgsetv1TestCase.aggregate)


class Tax1099msgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE", "TAX1099DNLD", "EXTD1099B", "TAXYEARSUPPORTED"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("TAX1099MSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "TAX1099DNLD").text = "Y"
        SubElement(root, "EXTD1099B").text = "Y"
        SubElement(root, "TAXYEARSUPPORTED").text = "2005"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return TAX1099MSGSETV1(msgsetcore=MsgsetcoreTestCase.aggregate,
                               tax1099dnld=True, extd1099b=True,
                               taxyearsupported=2005)


class Tax1099msgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("TAX1099MSGSET")
        root.append(Tax1099msgsetv1TestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return TAX1099MSGSET(tax1099msgsetv1=Tax1099msgsetv1TestCase.aggregate)


class MsgsetcoreTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    oneOfs = {"OFXSEC": ("NONE", "TYPE1"), "LANGUAGE": LANG_CODES,
              "SYNCMODE": ("FULL", "LITE")}

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

    @classproperty
    @classmethod
    def etree(cls):
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
        SubElement(root, "SPNAME").text = "Dewey Cheatham & Howe"
        root.append(OfxextensionTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MSGSETCORE(ver=1,
                          url="https://ofxs.ameritrade.com/cgi-bin/apps/OFX",
                          ofxsec="NONE", transpsec=True,
                          signonrealm="AMERITRADE", language="ENG",
                          syncmode="FULL", refreshsupt=False, respfileer=False,
                          spname="Dewey Cheatham & Howe",
                          ofxextension=OfxextensionTestCase.aggregate)


#  Test models.profile.MSGSETLIST here to avoid circular imports
class MsgsetlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return MSGSETLIST(SignonmsgsetTestCase.aggregate)

    @classproperty
    @classmethod
    def validSoup(cls):
        msgsets = [
            SignonmsgsetTestCase.etree,
            SignupmsgsetTestCase.etree,
            ProfmsgsetTestCase.etree,
            BankmsgsetTestCase.etree,
            CreditcardmsgsetTestCase.etree,
            InterxfermsgsetTestCase.etree,
            WirexfermsgsetTestCase.etree,
            InvstmtmsgsetTestCase.etree,
            SeclistmsgsetTestCase.etree,
            #  BillpaymsgsetTestCase.etree,
            Tax1099msgsetTestCase.etree,
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

    def testListItems(self):
        # MSGSETLIST may only contain
        # ["SIGNONMSGSET", "SIGNUPMSGSET", "PROFMSGSET", "BANKMSGSET",
        # "CREDITCARDMSGSET", "INTERXFERMSGSET", "WIREXFERMSGSET",
        # "INVSTMTMSGSET", "SECLISTMSGSET", "BILLPAYMSGSET", "PRESDIRMSGSET",
        # "PRESDLVMSGSET", "TAX1099MSGSET"]
        listitems = MSGSETLIST.listitems
        #  cls.assertEqual(len(listitems), 13)
        self.assertEqual(len(listitems), 11)
        root = self.etree
        root.append(StmttrnrsTestCase.etree)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


if __name__ == "__main__":
    unittest.main()
