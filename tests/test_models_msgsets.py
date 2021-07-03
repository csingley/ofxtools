# coding: utf-8
"""
Unit tests for models.msgsets
"""

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import time
from decimal import Decimal


# local imports
from ofxtools.models.base import Aggregate, UnknownTagWarning
from ofxtools.models.i18n import LANG_CODES
from ofxtools.models.signon import (
    SIGNONMSGSRQV1,
    SIGNONMSGSRSV1,
    SIGNONMSGSETV1,
    SIGNONMSGSET,
)
from ofxtools.models.profile import (
    MSGSETLIST,
    PROFMSGSRQV1,
    PROFMSGSRSV1,
    PROFMSGSETV1,
    PROFMSGSET,
)
from ofxtools.models.signup import (
    SIGNUPMSGSRQV1,
    SIGNUPMSGSRSV1,
    SIGNUPMSGSETV1,
    SIGNUPMSGSET,
)
from ofxtools.models.email import (
    EMAILMSGSRQV1,
    EMAILMSGSRSV1,
    EMAILMSGSETV1,
    EMAILMSGSET,
)
from ofxtools.models.bank.msgsets import (
    MSGSETCORE,
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
from ofxtools.models.bank.stmt import STMTRS
from ofxtools.models.bank.stmtend import STMTENDRS
from ofxtools.models.invest.msgsets import (
    INVSTMTMSGSRQV1,
    INVSTMTMSGSRSV1,
    INVSTMTMSGSETV1,
    INVSTMTMSGSET,
    SECLISTMSGSRQV1,
    SECLISTMSGSRSV1,
    SECLISTMSGSETV1,
    SECLISTMSGSET,
)
from ofxtools.models.tax1099 import TAX1099MSGSETV1, TAX1099MSGSET
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_common import OfxextensionTestCase
import test_models_signon as signon
import test_models_profile as profile
import test_models_email as email
import test_models_bank_stmt as bk_stmt
import test_models_bank_stmtend as bk_stmtend
import test_models_bank_stpchk as stpchk
import test_models_bank_xfer as xfer
import test_models_bank_interxfer as interxfer
import test_models_bank_wire as wire
import test_models_bank_recur as recur
import test_models_bank_mail as bank_mail
import test_models_bank_sync as bank_sync
import test_models_invest as invest
import test_models_securities as securities
import test_models_signup as signup


class Signonmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SONRQ"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONMSGSRQV1")
        root.append(signon.SonrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONMSGSRQV1(sonrq=signon.SonrqTestCase.aggregate)


class Signonmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SONRS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONMSGSRSV1")
        root.append(signon.SonrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONMSGSRSV1(sonrs=signon.SonrsTestCase.aggregate)


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
            root.append(profile.ProftrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFMSGSRQV1(
            profile.ProftrnrqTestCase.aggregate, profile.ProftrnrqTestCase.aggregate
        )

    def testListAggregate(self):
        # PROFMSGSRQV1 may only contain PROFTRNRQ
        listaggregates = PROFMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 1)
        root = self.etree
        root.append(profile.ProftrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Profmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFMSGSRSV1")
        for i in range(2):
            root.append(profile.ProftrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFMSGSRSV1(
            profile.ProftrnrsTestCase.aggregate, profile.ProftrnrsTestCase.aggregate
        )

    def testListAggregates(self):
        # PROFMSGSRSV1 may only contain PROFTRNRS
        listaggregates = PROFMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 1)
        root = self.etree
        root.append(profile.ProftrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
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
            root.append(signup.EnrolltrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSRQV1(
            signup.EnrolltrnrqTestCase.aggregate, signup.EnrolltrnrqTestCase.aggregate
        )

    def testListAggregates(self):
        # SIGNUPMSGSRQV1 may contain
        # ["ENROLLTRNRQ", "ACCTINFOTRNRQ", "ACCTTRNRQ", "CHGUSERINFOTRNRQ"]
        listaggregates = SIGNUPMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 4)
        root = self.etree
        root.append(signup.EnrolltrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Signupmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNUPMSGSRSV1")
        for i in range(2):
            root.append(signup.EnrolltrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSRSV1(
            signup.EnrolltrnrsTestCase.aggregate, signup.EnrolltrnrsTestCase.aggregate
        )

    def testListAggregates(self):
        # SIGNUPMSGSRSV1 may contain
        # ["ENROLLTRNRS", "ACCTINFOTRNRS", "ACCTTRNRS", "CHGUSERINFOTRNRS"]
        listaggregates = SIGNUPMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 4)
        root = self.etree
        root.append(signup.EnrolltrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Signupmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MSGSETCORE", "CHGUSERINFO", "AVAILACCTS", "CLIENTACTREQ"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNUPMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        root.append(signup.WebenrollTestCase.etree)
        SubElement(root, "CHGUSERINFO").text = "N"
        SubElement(root, "AVAILACCTS").text = "Y"
        SubElement(root, "CLIENTACTREQ").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNUPMSGSETV1(
            msgsetcore=MsgsetcoreTestCase.aggregate,
            webenroll=signup.WebenrollTestCase.aggregate,
            chguserinfo=False,
            availaccts=True,
            clientactreq=False,
        )


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
        for rq in (
            email.MailtrnrqTestCase,
            email.GetmimetrnrqTestCase,
            email.MailsyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILMSGSRQV1(
            email.MailtrnrqTestCase.aggregate,
            email.MailtrnrqTestCase.aggregate,
            email.GetmimetrnrqTestCase.aggregate,
            email.GetmimetrnrqTestCase.aggregate,
            email.MailsyncrqTestCase.aggregate,
            email.MailsyncrqTestCase.aggregate,
        )

    def testListAggregates(self):
        # EMAILMSGSRQV1 may contain ["MAILTRNRQ", "GETMIMETRNRQ", "MAILSYNCRQ"]
        listaggregates = EMAILMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 3)
        root = self.etree
        root.append(email.MailtrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Emailmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EMAILMSGSRSV1")
        for rs in (
            email.MailtrnrsTestCase,
            email.GetmimetrnrsTestCase,
            email.MailsyncrsTestCase,
        ):
            for i in range(2):
                root.append(rs.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EMAILMSGSRSV1(
            email.MailtrnrsTestCase.aggregate,
            email.MailtrnrsTestCase.aggregate,
            email.GetmimetrnrsTestCase.aggregate,
            email.GetmimetrnrsTestCase.aggregate,
            email.MailsyncrsTestCase.aggregate,
            email.MailsyncrsTestCase.aggregate,
        )

    def testListAggregates(self):
        # EMAILMSGSRSV1 may contain ["MAILTRNRS", "GETMIMETRNRS", "MAILSYNCRS"]
        listaggregates = EMAILMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 3)
        root = self.etree
        root.append(email.MailtrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
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
        return EMAILMSGSETV1(
            msgsetcore=MsgsetcoreTestCase.aggregate, mailsup=True, getmimesup=True
        )


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
            bk_stmt.StmttrnrqTestCase,
            bk_stmtend.StmtendtrnrqTestCase,
            stpchk.StpchktrnrqTestCase,
            xfer.IntratrnrqTestCase,
            recur.RecintratrnrqTestCase,
            bank_mail.BankmailtrnrqTestCase,
            bank_sync.StpchksyncrqTestCase,
            bank_sync.IntrasyncrqTestCase,
            bank_sync.RecintrasyncrqTestCase,
            bank_sync.BankmailsyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSRQV1(
            bk_stmt.StmttrnrqTestCase.aggregate,
            bk_stmt.StmttrnrqTestCase.aggregate,
            bk_stmtend.StmtendtrnrqTestCase.aggregate,
            bk_stmtend.StmtendtrnrqTestCase.aggregate,
            stpchk.StpchktrnrqTestCase.aggregate,
            stpchk.StpchktrnrqTestCase.aggregate,
            xfer.IntratrnrqTestCase.aggregate,
            xfer.IntratrnrqTestCase.aggregate,
            recur.RecintratrnrqTestCase.aggregate,
            recur.RecintratrnrqTestCase.aggregate,
            bank_mail.BankmailtrnrqTestCase.aggregate,
            bank_mail.BankmailtrnrqTestCase.aggregate,
            bank_sync.StpchksyncrqTestCase.aggregate,
            bank_sync.StpchksyncrqTestCase.aggregate,
            bank_sync.IntrasyncrqTestCase.aggregate,
            bank_sync.IntrasyncrqTestCase.aggregate,
            bank_sync.RecintrasyncrqTestCase.aggregate,
            bank_sync.RecintrasyncrqTestCase.aggregate,
            bank_sync.BankmailsyncrqTestCase.aggregate,
            bank_sync.BankmailsyncrqTestCase.aggregate,
        )

    def testListAggregates(self):
        # BANKMSGSRQV1 may contain
        # ["STMTTRNRQ", "STMTENDTRNRQ", "STPCHKTRNRQ", "INTRATRNRQ",
        # "RECINTRATRNRQ", "BANKMAILTRNRQ", "STPCHKSYNCRQ", "INTRASYNCRQ",
        # "RECINTRASYNCRQ", "BANKMAILSYNCRQ"]

        listaggregates = BANKMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 10)
        root = self.etree
        root.append(bk_stmt.StmttrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Bankmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKMSGSRSV1")
        for rs in (
            bk_stmt.StmttrnrsTestCase,
            bk_stmtend.StmtendtrnrsTestCase,
            stpchk.StpchktrnrsTestCase,
            xfer.IntratrnrsTestCase,
            recur.RecintratrnrsTestCase,
            bank_mail.BankmailtrnrsTestCase,
            bank_sync.StpchksyncrsTestCase,
            bank_sync.IntrasyncrsTestCase,
            bank_sync.RecintrasyncrsTestCase,
            bank_sync.BankmailsyncrsTestCase,
        ):
            for i in range(2):
                root.append(rs.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSRSV1(
            bk_stmt.StmttrnrsTestCase.aggregate,
            bk_stmt.StmttrnrsTestCase.aggregate,
            bk_stmtend.StmtendtrnrsTestCase.aggregate,
            bk_stmtend.StmtendtrnrsTestCase.aggregate,
            stpchk.StpchktrnrsTestCase.aggregate,
            stpchk.StpchktrnrsTestCase.aggregate,
            xfer.IntratrnrsTestCase.aggregate,
            xfer.IntratrnrsTestCase.aggregate,
            recur.RecintratrnrsTestCase.aggregate,
            recur.RecintratrnrsTestCase.aggregate,
            bank_mail.BankmailtrnrsTestCase.aggregate,
            bank_mail.BankmailtrnrsTestCase.aggregate,
            bank_sync.StpchksyncrsTestCase.aggregate,
            bank_sync.StpchksyncrsTestCase.aggregate,
            bank_sync.IntrasyncrsTestCase.aggregate,
            bank_sync.IntrasyncrsTestCase.aggregate,
            bank_sync.RecintrasyncrsTestCase.aggregate,
            bank_sync.RecintrasyncrsTestCase.aggregate,
            bank_sync.BankmailsyncrsTestCase.aggregate,
            bank_sync.BankmailsyncrsTestCase.aggregate,
        )

    def testListAggregates(self):
        # BANKMSGSRSV! may contain
        # ["STMTTRNRS", "STMTENDRS", "STPCHKTRNRS", "INTRATRNRS",
        # "RECINTRATRNRS", "BANKMAILTRNRS", "STPCHKSYNCRS", "INTRASYNCRS",
        # "RECINTRASYNCRS", "BANKMAILSYNCRS"]
        listaggregates = BANKMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 10)
        root = self.etree
        root.append(bk_stmt.StmttrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertIsInstance(instance.statements, list)
        self.assertEqual(len(instance.statements), 4)
        self.assertIsInstance(instance.statements[0], STMTRS)
        self.assertIsInstance(instance.statements[1], STMTRS)
        self.assertIsInstance(instance.statements[2], STMTENDRS)
        self.assertIsInstance(instance.statements[3], STMTENDRS)


class XferprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("XFERPROF")
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000.000[+0:UTC]"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "CANRECUR").text = "Y"
        SubElement(root, "CANMODXFERS").text = "N"
        SubElement(root, "CANMODMDLS").text = "Y"
        SubElement(root, "MODELWND").text = "3"
        SubElement(root, "DAYSWITH").text = "2"
        SubElement(root, "DFLTDAYSTOPAY").text = "4"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return XFERPROF(
            "SUNDAY",
            procendtm=time(17, 0, 0, tzinfo=UTC),
            cansched=True,
            canrecur=True,
            canmodxfers=False,
            canmodmdls=True,
            modelwnd=3,
            dayswith=2,
            dfltdaystopay=4,
        )


class StpchkprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STPCHKPROF")
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000.000[+0:UTC]"
        SubElement(root, "CANUSERANGE").text = "Y"
        SubElement(root, "CANUSEDESC").text = "Y"
        SubElement(root, "STPCHKFEE").text = "30.1"

        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STPCHKPROF(
            "SUNDAY",
            procendtm=time(17, 0, 0, tzinfo=UTC),
            canuserange=True,
            canusedesc=True,
            stpchkfee=Decimal("30.1"),
        )


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

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "INVALIDACCTTYPE").text = "CHECKING"
        SubElement(root, "INVALIDACCTTYPE").text = "SAVINGS"
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        SubElement(root, "PENDINGAVAIL").text = "N"
        root.append(XferprofTestCase.etree)
        root.append(StpchkprofTestCase.etree)
        root.append(EmailprofTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKMSGSETV1(
            "CHECKING",
            "SAVINGS",
            msgsetcore=MsgsetcoreTestCase.aggregate,
            closingavail=True,
            pendingavail=False,
            xferprof=XferprofTestCase.aggregate,
            stpchkprof=StpchkprofTestCase.aggregate,
            emailprof=EmailprofTestCase.aggregate,
        )


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
        root.append(bk_stmt.CcstmttrnrqTestCase.etree)
        root.append(bk_stmtend.CcstmtendtrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CREDITCARDMSGSRQV1(
            bk_stmt.CcstmttrnrqTestCase.aggregate,
            bk_stmtend.CcstmtendtrnrqTestCase.aggregate,
        )


class Creditcardmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CREDITCARDMSGSRSV1")
        root.append(bk_stmt.CcstmttrnrsTestCase.etree)
        root.append(bk_stmtend.CcstmtendtrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CREDITCARDMSGSRSV1(
            bk_stmt.CcstmttrnrsTestCase.aggregate,
            bk_stmtend.CcstmtendtrnrsTestCase.aggregate,
        )


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
        return CREDITCARDMSGSETV1(
            msgsetcore=MsgsetcoreTestCase.aggregate,
            closingavail=True,
            pendingavail=False,
        )


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
            interxfer.IntertrnrqTestCase,
            recur.RecintertrnrqTestCase,
            bank_sync.IntersyncrqTestCase,
            bank_sync.RecintersyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERXFERMSGSRQV1(
            interxfer.IntertrnrqTestCase.aggregate,
            interxfer.IntertrnrqTestCase.aggregate,
            recur.RecintertrnrqTestCase.aggregate,
            recur.RecintertrnrqTestCase.aggregate,
            bank_sync.IntersyncrqTestCase.aggregate,
            bank_sync.IntersyncrqTestCase.aggregate,
            bank_sync.RecintersyncrqTestCase.aggregate,
            bank_sync.RecintersyncrqTestCase.aggregate,
        )

    def testListAggregates(self):
        # INTERXFERMSGSRQV1 may contain
        # ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]
        listaggregates = INTERXFERMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 4)
        root = self.etree
        root.append(interxfer.IntertrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Interxfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INTERXFERMSGSRSV1")
        for rq in (
            interxfer.IntertrnrsTestCase,
            recur.RecintertrnrsTestCase,
            bank_sync.IntersyncrsTestCase,
            bank_sync.RecintersyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INTERXFERMSGSRSV1(
            interxfer.IntertrnrsTestCase.aggregate,
            interxfer.IntertrnrsTestCase.aggregate,
            recur.RecintertrnrsTestCase.aggregate,
            recur.RecintertrnrsTestCase.aggregate,
            bank_sync.IntersyncrsTestCase.aggregate,
            bank_sync.IntersyncrsTestCase.aggregate,
            bank_sync.RecintersyncrsTestCase.aggregate,
            bank_sync.RecintersyncrsTestCase.aggregate,
        )

    def testListAggregates(self):
        # INTERXFERMSGSRSV1 may contain
        # ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]
        listaggregates = INTERXFERMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 4)
        root = self.etree
        root.append(interxfer.IntertrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
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
        return INTERXFERMSGSETV1(
            msgsetcore=MsgsetcoreTestCase.aggregate,
            xferprof=XferprofTestCase.aggregate,
            canbillpay=True,
            cancwnd=2,
            domxferfee=Decimal("7.50"),
            intlxferfee=Decimal("17.50"),
        )


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
        for rq in (wire.WiretrnrqTestCase, bank_sync.WiresyncrqTestCase):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSRQV1(
            wire.WiretrnrqTestCase.aggregate,
            wire.WiretrnrqTestCase.aggregate,
            bank_sync.WiresyncrqTestCase.aggregate,
            bank_sync.WiresyncrqTestCase.aggregate,
        )

    def testListAggregates(self):
        # WIREXFERMSGSRQV1 may contain
        # ["WIRETRNRQ", "WIREERSYNCRQ"]
        listaggregates = WIREXFERMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 2)
        root = self.etree
        root.append(wire.WiretrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Wirexfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREXFERMSGSRSV1")
        for rq in (wire.WiretrnrsTestCase, bank_sync.WiresyncrsTestCase):
            for i in range(2):
                root.append(rq.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSRSV1(
            wire.WiretrnrsTestCase.aggregate,
            wire.WiretrnrsTestCase.aggregate,
            bank_sync.WiresyncrsTestCase.aggregate,
            bank_sync.WiresyncrsTestCase.aggregate,
        )

    def testListAggregates(self):
        # WIRERXFERMSGSRSV1 may contain
        # ["WIRETRNRS", "WIRESYNCRS"]
        listaggregates = WIREXFERMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 2)
        root = self.etree
        root.append(wire.WiretrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Wirexfermsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WIREXFERMSGSETV1")
        root.append(MsgsetcoreTestCase.etree)
        SubElement(root, "PROCDAYSOFF").text = "SUNDAY"
        SubElement(root, "PROCENDTM").text = "170000.000[+0:UTC]"
        SubElement(root, "CANSCHED").text = "Y"
        SubElement(root, "DOMXFERFEE").text = "7.50"
        SubElement(root, "INTLXFERFEE").text = "17.50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WIREXFERMSGSETV1(
            "SUNDAY",
            msgsetcore=MsgsetcoreTestCase.aggregate,
            procendtm=time(17, 0, 0, tzinfo=UTC),
            cansched=True,
            domxferfee=Decimal("7.50"),
            intlxferfee=Decimal("17.50"),
        )


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

#  def testListAggregates(self):
#  # BILLPAYMSGSRQV1 may contain
#  # [PMTTRNRQ, RECPMTTRNRQ, PAYEETRNRQ, PMTINQTRNRQ, PMTMAILTRNRQ,
#  # PMTSYNCRQ, RECPMTSYNCRQ, PAYEESYNCRQ, PMTMAILSYNCRQ]
#  listaggregates = BILLPAYMSGSRQV1.listaggregates
#  self.assertEqual(len(listaggregates), 9)
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

#  def testListAggregates(self):
#  # BILLPAYMSGSRQV1 may contain
#  # [PMTTRNRS, RECPMTTRNRS, PAYEETRNRS, PMTINQTRNRS, PMTMAILTRNRS,
#  # PMTSYNCRS, RECPMTSYNCRS, PAYEESYNCRS, PMTMAILSYNCRS]
#  listaggregates = BILLPAYMSGSRSV1.listaggregates
#  self.assertEqual(len(listaggregates), 9)
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
#  SubElement(root, "PROCENDTM").text = "170000.000[+0:UTC]"
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
            stmttrnrq = invest.InvstmttrnrqTestCase.etree
            root.append(stmttrnrq)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTMSGSRQV1(
            invest.InvstmttrnrqTestCase.aggregate, invest.InvstmttrnrqTestCase.aggregate
        )

    def testListAggregates(self):
        # INVSTMTMSGSRQV1 may only contain
        # ["INVSTMTTRNRQ", "INVMAILTRNRQ", "INVMAILSYNCRQ"]
        listaggregates = INVSTMTMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 3)
        root = self.etree
        root.append(invest.InvstmttrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Invstmtmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTMSGSRSV1")
        for i in range(2):
            stmttrnrs = invest.InvstmttrnrsTestCase.etree
            root.append(stmttrnrs)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTMSGSRSV1(
            invest.InvstmttrnrsTestCase.aggregate, invest.InvstmttrnrsTestCase.aggregate
        )

    def testListAggregates(self):
        # INVSTMTMSGSRSV1 may only contain
        # ["INVSTMTTRNRS", "INVMAILTRNRS", "INVMAILSYNCRS"]
        listaggregates = INVSTMTMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 3)
        root = self.etree
        root.append(invest.InvstmttrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
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
        return INVSTMTMSGSETV1(
            msgsetcore=MsgsetcoreTestCase.aggregate,
            trandnld=True,
            oodnld=True,
            posdnld=True,
            baldnld=True,
            canemail=False,
            inv401kdnld=False,
            closingavail=True,
        )


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
            root.append(securities.SeclisttrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTMSGSRQV1(
            securities.SeclisttrnrqTestCase.aggregate,
            securities.SeclisttrnrqTestCase.aggregate,
        )

    def testListAggregates(self):
        # SECLISTMSGSRQV1 may only contain SECLISTTRNRQ

        listaggregates = SECLISTMSGSRQV1.listaggregates
        self.assertEqual(len(listaggregates), 1)
        root = self.etree
        root.append(securities.SeclisttrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class Seclistmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    # FIXME
    # requiredElements = ('SECLIST',)

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLISTMSGSRSV1")
        root.append(securities.SeclistTestCase.etree)
        root.append(securities.SeclistTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTMSGSRSV1(
            securities.SeclistTestCase.aggregate, securities.SeclistTestCase.aggregate
        )

    def testListAggregates(self):
        # SECLISTMSGSRSV1 may only contain SECLISTTRNRS, SECLIST

        listaggregates = SECLISTMSGSRSV1.listaggregates
        self.assertEqual(len(listaggregates), 2)
        root = self.etree
        root.append(securities.SeclisttrnrqTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
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
        return SECLISTMSGSETV1(
            msgsetcore=MsgsetcoreTestCase.aggregate, seclistrqdnld=False
        )


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
        return TAX1099MSGSETV1(
            2005,
            msgsetcore=MsgsetcoreTestCase.aggregate,
            tax1099dnld=True,
            extd1099b=True,
        )


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

    oneOfs = {
        "OFXSEC": ("NONE", "TYPE1"),
        "LANGUAGE": LANG_CODES,
        "SYNCMODE": ("FULL", "LITE"),
    }

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
        return MSGSETCORE(
            "ENG",
            ver=1,
            url="https://ofxs.ameritrade.com/cgi-bin/apps/OFX",
            ofxsec="NONE",
            transpsec=True,
            signonrealm="AMERITRADE",
            syncmode="FULL",
            refreshsupt=False,
            respfileer=False,
            spname="Dewey Cheatham & Howe",
            ofxextension=OfxextensionTestCase.aggregate,
        )


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
            BankmsgsetTestCase.etree,
            CreditcardmsgsetTestCase.etree,
            InvstmtmsgsetTestCase.etree,
            InterxfermsgsetTestCase.etree,
            WirexfermsgsetTestCase.etree,
            EmailmsgsetTestCase.etree,
            SeclistmsgsetTestCase.etree,
            #  BillpaymsgsetTestCase.etree,
            ProfmsgsetTestCase.etree,
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

    def testListAggregates(self):
        # MSGSETLIST may only contain
        # ["SIGNONMSGSET", "SIGNUPMSGSET", "PROFMSGSET", "BANKMSGSET",
        # "CREDITCARDMSGSET", "INTERXFERMSGSET", "WIREXFERMSGSET",
        # "EMAILMSGSET", "INVSTMTMSGSET", "SECLISTMSGSET", "BILLPAYMSGSET",
        # "PRESDIRMSGSET", "PRESDLVMSGSET", "TAX1099MSGSET"]
        listaggregates = MSGSETLIST.listaggregates
        self.assertEqual(len(listaggregates), 12)
        root = self.etree
        root.append(bk_stmt.StmttrnrsTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


if __name__ == "__main__":
    unittest.main()
