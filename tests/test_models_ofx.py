# coding: utf-8
""" Unit tests for models.ofx """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element
from datetime import datetime


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.ofx import OFX
from ofxtools.models.signon import SIGNONMSGSRSV1
from ofxtools.models.bank import BANKMSGSRSV1, CREDITCARDMSGSRSV1
from ofxtools.models.invest import INVSTMTMSGSRSV1, SECLISTMSGSRSV1
from ofxtools.models.signon import SONRS
from ofxtools.models.bank import STMTRS, CCSTMTRS, CCSTMTENDRS
from ofxtools.models.invest import INVSTMTRS
from ofxtools.utils import UTC, classproperty


# test imports
import base


from test_models_msgsets import (
    Signonmsgsrqv1TestCase,
    Signonmsgsrsv1TestCase,
    Profmsgsrqv1TestCase,
    Profmsgsrsv1TestCase,
    Signupmsgsrqv1TestCase,
    Signupmsgsrsv1TestCase,
    Emailmsgsrqv1TestCase,
    Emailmsgsrsv1TestCase,
    Bankmsgsrqv1TestCase,
    Bankmsgsrsv1TestCase,
    Creditcardmsgsrqv1TestCase,
    Creditcardmsgsrsv1TestCase,
    Interxfermsgsrqv1TestCase,
    Interxfermsgsrsv1TestCase,
    Wirexfermsgsrqv1TestCase,
    Wirexfermsgsrsv1TestCase,
    Invstmtmsgsrqv1TestCase,
    Invstmtmsgsrsv1TestCase,
    Seclistmsgsrqv1TestCase,
    Seclistmsgsrsv1TestCase,
)


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
            (
                Signonmsgsrqv1TestCase,
                [
                    Signupmsgsrqv1TestCase,
                    Bankmsgsrqv1TestCase,
                    Creditcardmsgsrqv1TestCase,
                    Invstmtmsgsrqv1TestCase,
                    Interxfermsgsrqv1TestCase,
                    Wirexfermsgsrqv1TestCase,
                    Emailmsgsrqv1TestCase,
                    Seclistmsgsrqv1TestCase,
                    Profmsgsrqv1TestCase,
                ],
            ),
            (
                Signonmsgsrsv1TestCase,
                [
                    Signupmsgsrsv1TestCase,
                    Bankmsgsrsv1TestCase,
                    Creditcardmsgsrsv1TestCase,
                    Invstmtmsgsrsv1TestCase,
                    Interxfermsgsrsv1TestCase,
                    Wirexfermsgsrsv1TestCase,
                    Emailmsgsrsv1TestCase,
                    Seclistmsgsrsv1TestCase,
                    Profmsgsrsv1TestCase,
                ],
            ),
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
        signonmsgsrqv1 = Signonmsgsrqv1TestCase().root
        signonmsgsrsv1 = Signonmsgsrsv1TestCase().root
        signupmsgsrqv1 = Signupmsgsrqv1TestCase().root
        signupmsgsrsv1 = Signupmsgsrsv1TestCase().root

        # Neither SIGNONMSGSRQV1 nor SIGNONMSGSRSV1
        root = Element("OFX")
        yield root

        # Both SIGNONMSGSRQV1 and SIGNONMSGSRSV1
        root = Element("OFX")
        root.append(signonmsgsrqv1)
        root.append(signonmsgsrsv1)
        yield root

        # Mixed *MSGSRQV1 and *MSGSRSV1
        root = Element("OFX")
        root.append(signonmsgsrqv1)
        root.append(signupmsgsrsv1)
        yield root

        root = Element("OFX")
        root.append(signonmsgsrsv1)
        root.append(signupmsgsrqv1)
        yield root

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    @property
    def root(self):
        return list(self.validSoup)[-1]

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
        # 5 securitites each from 2 SECLISTs in test_models_securities.SeclistTestCase
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
