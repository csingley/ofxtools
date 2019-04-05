# coding: utf-8
""" Unit tests for models/messages.py """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element
from datetime import datetime


# local imports
import base
from test_models_signon import Signonmsgsrqv1TestCase, Signonmsgsrsv1TestCase
from test_models_signup import Signupmsgsrqv1TestCase, Signupmsgsrsv1TestCase
from test_models_bank import (Bankmsgsrqv1TestCase, Bankmsgsrsv1TestCase)
from test_models_creditcard import Creditcardmsgsrqv1TestCase, Creditcardmsgsrsv1TestCase
from test_models_interxfer import Interxfermsgsrqv1TestCase, Interxfermsgsrsv1TestCase
from test_models_wire import Wirexfermsgsrqv1TestCase, Wirexfermsgsrsv1TestCase
from test_models_email import Emailmsgsrqv1TestCase, Emailmsgsrsv1TestCase
from test_models_investment import Invstmtmsgsrqv1TestCase, Invstmtmsgsrsv1TestCase
from test_models_seclist import Seclistmsgsrqv1TestCase, Seclistmsgsrsv1TestCase
from test_models_profile import Profmsgsrqv1TestCase, Profmsgsrsv1TestCase

from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.ofx import OFX
from ofxtools.models.signon import SIGNONMSGSRSV1, SONRS
from ofxtools.models.bank import (
    BANKMSGSRSV1, STMTRS, CREDITCARDMSGSRSV1, CCSTMTRS, CCSTMTENDRS
)
from ofxtools.models.investment import INVSTMTMSGSRSV1, INVSTMTRS
from ofxtools.models.seclist import SECLISTMSGSRSV1

from ofxtools.utils import UTC


class OfxTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    unsupported = [
        "billpaymsgsrqv1",
        "billpaymsgsrsv1",
        "presdirmsgsrqv1",
        "presdirmsgsrsv1",
        "presdlvmsgsrqv1",
        "presdlvmsgsrsv1",
        "loanmsgsrqv1",
        "loanmsgsrsv1",
        "tax1098msgsrqv1",
        "tax1098msgsrsv1",
        "tax1099msgsrqv1",
        "tax1099msgsrsv1",
        "taxw2msgsrqv1",
        "taxw2msgsrsv1",
        "tax1095msgsrqv1",
        "tax1095msgsrsv1",
    ]

    @classproperty
    @classmethod
    def validSoup(cls):
        for signonmsgs, optionalmsgs in [
            (Signonmsgsrqv1TestCase, [
                Signupmsgsrqv1TestCase, Bankmsgsrqv1TestCase,
                Creditcardmsgsrqv1TestCase, Invstmtmsgsrqv1TestCase,
                Interxfermsgsrqv1TestCase, Wirexfermsgsrqv1TestCase,
                Emailmsgsrqv1TestCase, Seclistmsgsrqv1TestCase,
                Profmsgsrqv1TestCase
            ]),
            (Signonmsgsrsv1TestCase, [
                Signupmsgsrsv1TestCase, Bankmsgsrsv1TestCase,
                Creditcardmsgsrsv1TestCase, Invstmtmsgsrsv1TestCase,
                Interxfermsgsrsv1TestCase, Wirexfermsgsrsv1TestCase,
                Emailmsgsrsv1TestCase, Seclistmsgsrsv1TestCase,
                Profmsgsrsv1TestCase
            ])
        ]:
            root = Element("OFX")
            root.append(signonmsgs().root)
            yield root
            for msgs in optionalmsgs:
                root.append(msgs().root)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [("signonmsgsrqv1", "signonmsgsrsv1")]
        #  optionalMutexes = [
            #  ("signupmsgsrqv1", "signupmsgsrsv1"),
            #  ("bankmsgsrqv1", "bankmsgsrsv1"),
            #  ("creditcardmsgsrqv1", "creditcardmsgsrsv1"),
            #  ("invstmtmsgsrqv1", "invstmtmsgsrsv1"),
            #  ("interxfermsgsrqv1", "interxfermsgsrsv1"),
            #  ("wirexfermsgsrqv1", "wirexfermsgsrsv1"),
            #  #  ("billpaymsgsrqv1", "billpaymsgsrsv1"),
            #  ("emailmsgsrqv1", "emailmsgsrsv1"),
            #  ("seclistmsgsrqv1", "seclistmsgsrsv1"),
            #  #  ("presdirmsgsrqv1", "presdirmsgsrsv1"),
            #  #  ("presdlmsgsrqv1", "presdlmsgsrsv1"),
            #  ("profmsgsrqv1", "profmsgsrsv1"),
            #  #  ("loanmsgsrqv1", "loanmsgsrsv1"),
            #  #  ("tax1098msgsrqv1", "tax1098msgsrsv1"),
            #  #  ("tax1099msgsrqv1", "tax1099msgsrsv1"),
            #  #  ("taxw2msgsrqv1", "taxw2msgsrsv1"),
            #  #  ("tax1095msgsrqv1", "tax1095msgsrsv1"),
            #  # Don't allow mixed *RQ and *RS in the same OFX
            #  ("signupmsgsrqv1", "bankmsgsrsv1"),
            #  ("signupmsgsrqv1", "creditcardmsgsrsv1"),
            #  ("signupmsgsrqv1", "invstmtmsgsrsv1"),
            #  ("signupmsgsrqv1", "interxfermsgsrsv1"),
            #  ("signupmsgsrqv1", "wirexfermsgsrsv1"),
            #  ("signupmsgsrqv1", "billpaymsgsrsv1"),
            #  ("signupmsgsrqv1", "emailmsgsrsv1"),
            #  ("signupmsgsrqv1", "seclistmsgsrsv1"),
            #  ("signupmsgsrqv1", "presdirmsgsrsv1"),
            #  ("signupmsgsrqv1", "presdlmsgsrsv1"),
            #  ("signupmsgsrqv1", "profmsgsrsv1"),
            #  ("signupmsgsrqv1", "loanmsgsrsv1"),
            #  ("signupmsgsrqv1", "tax1098msgsrsv1"),
            #  ("signupmsgsrqv1", "tax1099msgsrsv1"),
            #  ("signupmsgsrqv1", "taxw2msgsrsv1"),
            #  ("signupmsgsrqv1", "tax1095msgsrsv1"),
            #  ("signupmsgsrsv1", "bankmsgsrqv1"),
            #  ("signupmsgsrsv1", "creditcardmsgsrqv1"),
            #  ("signupmsgsrsv1", "invstmtmsgsrqv1"),
            #  ("signupmsgsrsv1", "interxfermsgsrqv1"),
            #  ("signupmsgsrsv1", "wirexfermsgsrqv1"),
            #  ("signupmsgsrsv1", "billpaymsgsrqv1"),
            #  ("signupmsgsrsv1", "emailmsgsrqv1"),
            #  ("signupmsgsrsv1", "seclistmsgsrqv1"),
            #  ("signupmsgsrsv1", "presdirmsgsrqv1"),
            #  ("signupmsgsrsv1", "presdlmsgsrqv1"),
            #  ("signupmsgsrsv1", "profmsgsrqv1"),
            #  ("signupmsgsrsv1", "loanmsgsrqv1"),
            #  ("signupmsgsrsv1", "tax1098msgsrqv1"),
            #  ("signupmsgsrsv1", "tax1099msgsrqv1"),
            #  ("signupmsgsrsv1", "taxw2msgsrqv1"),
            #  ("signupmsgsrsv1", "tax1095msgsrqv1")
        #  ]
        # FIXME
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    @property
    def root(self):
        #  root = Element("OFX")
        #  for msg in (
            #  test_models_signon.Signonmsgsrsv1TestCase,
            #  test_models_bank.Bankmsgsrsv1TestCase,
            #  test_models_creditcard.Creditcardmsgsrsv1TestCase,
            #  test_models_investment.Invstmtmsgsrsv1TestCase,
            #  test_models_seclist.Seclistmsgsrsv1TestCase,
        #  ):
            #  root.append(msg().root)
        #  return root
        return list(self.validSoup)[-1]

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, OFX)
        self.assertIsInstance(instance.signonmsgsrsv1, SIGNONMSGSRSV1)
        self.assertIsInstance(instance.bankmsgsrsv1, BANKMSGSRSV1)
        self.assertIsInstance(instance.creditcardmsgsrsv1, CREDITCARDMSGSRSV1)
        self.assertIsInstance(instance.invstmtmsgsrsv1, INVSTMTMSGSRSV1)
        self.assertIsInstance(instance.seclistmsgsrsv1, SECLISTMSGSRSV1)

    def testUnsupported(self):
        instance = Aggregate.from_etree(self.root)
        unsupported = list(instance.unsupported)
        self.assertEqual(unsupported, self.unsupported)
        for unsupp in unsupported:
            setattr(instance, unsupp, "FOOBAR")
            self.assertIsNone(getattr(instance, unsupp))

    def testRepr(self):
        instance = Aggregate.from_etree(self.root)
        rep = repr(instance)
        rep_template = (
            "<OFX fid='{fid}' org='{org}' dtserver='{dtserver}' "
            "len(statements)={stmtlen} len(securities)={seclen}>"
        )
        # SIGNON values from test_models_signon.FiTestCase
        # DTSERVER from test_models_signon.SonrsTestCase
        # 2 *STMTs each from bank/cc/invstmt (6 total)
        # 5 securitites each from 2 SECLISTs in test_models_seclist.SeclistTestCase
        rep_values = {
            "fid": "4705",
            "org": "IBLLC-US",
            "dtserver": datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
            "stmtlen": 6,
            "seclen": 10,
        }
        self.assertEqual(rep, rep_template.format(**rep_values))

    def testPropertyAliases(self):
        # Make sure class property aliases have been defined correctly
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, OFX)
        self.assertIsInstance(instance.sonrs, SONRS)
        self.assertIsInstance(instance.securities, list)
        self.assertIsInstance(instance.statements, list)
        # *MSGSRSV1 test cases include 2 of each *STMTRS
        self.assertEqual(len(instance.statements), 6)
        self.assertIsInstance(instance.statements[0], STMTRS)
        self.assertIsInstance(instance.statements[1], STMTRS)
        self.assertIsInstance(instance.statements[2], CCSTMTRS)
        self.assertIsInstance(instance.statements[3], CCSTMTENDRS)
        self.assertIsInstance(instance.statements[4], INVSTMTRS)
        self.assertIsInstance(instance.statements[5], INVSTMTRS)


if __name__ == "__main__":
    unittest.main()
