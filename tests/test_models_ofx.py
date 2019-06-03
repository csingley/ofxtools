# coding: utf-8
""" Unit tests for models.ofx """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element
from datetime import datetime


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.ofx import OFX
from ofxtools.models.signon import SONRS
from ofxtools.models.bank import STMTRS, CCSTMTRS, STMTENDRS, CCSTMTENDRS
from ofxtools.models.invest import INVSTMTRS
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_msgsets as msgsets


# Cache results of expensive class properties for reuse
signonmsgsrqv1 = msgsets.Signonmsgsrqv1TestCase.etree
signupmsgsrqv1 = msgsets.Signupmsgsrqv1TestCase.etree
bankmsgsrqv1 = msgsets.Bankmsgsrqv1TestCase.etree
creditcardmsgsrqv1 = msgsets.Creditcardmsgsrqv1TestCase.etree
invstmtmsgsrqv1 = msgsets.Invstmtmsgsrqv1TestCase.etree
interxfermsgsrqv1 = msgsets.Interxfermsgsrqv1TestCase.etree
wirexfermsgsrqv1 = msgsets.Wirexfermsgsrqv1TestCase.etree
emailmsgsrqv1 = msgsets.Emailmsgsrqv1TestCase.etree
seclistmsgsrqv1 = msgsets.Seclistmsgsrqv1TestCase.etree
profmsgsrqv1 = msgsets.Profmsgsrqv1TestCase.etree

signonmsgsrsv1 = msgsets.Signonmsgsrsv1TestCase.etree
signupmsgsrsv1 = msgsets.Signupmsgsrsv1TestCase.etree
bankmsgsrsv1 = msgsets.Bankmsgsrsv1TestCase.etree
creditcardmsgsrsv1 = msgsets.Creditcardmsgsrsv1TestCase.etree
invstmtmsgsrsv1 = msgsets.Invstmtmsgsrsv1TestCase.etree
interxfermsgsrsv1 = msgsets.Interxfermsgsrsv1TestCase.etree
wirexfermsgsrsv1 = msgsets.Wirexfermsgsrsv1TestCase.etree
emailmsgsrsv1 = msgsets.Emailmsgsrsv1TestCase.etree
seclistmsgsrsv1 = msgsets.Seclistmsgsrsv1TestCase.etree
profmsgsrsv1 = msgsets.Profmsgsrsv1TestCase.etree


class OfxTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    unsupported = [
        "presdirmsgsrqv1",
        "presdirmsgsrsv1",
        "presdlvmsgsrqv1",
        "presdlvmsgsrsv1",
        "loanmsgsrqv1",
        "loanmsgsrsv1",
        "tax1098msgsrqv1",
        "tax1098msgsrsv1",
        "taxw2msgsrqv1",
        "taxw2msgsrsv1",
        "tax1095msgsrqv1",
        "tax1095msgsrsv1",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("OFX")
        root.append(signonmsgsrqv1)
        root.append(signupmsgsrqv1)
        root.append(bankmsgsrqv1)
        root.append(creditcardmsgsrqv1)
        root.append(invstmtmsgsrqv1)
        root.append(interxfermsgsrqv1)
        root.append(wirexfermsgsrqv1)
        root.append(emailmsgsrqv1)
        root.append(seclistmsgsrqv1)
        root.append(profmsgsrqv1)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return OFX(
            signonmsgsrqv1=msgsets.Signonmsgsrqv1TestCase.aggregate,
            signupmsgsrqv1=msgsets.Signupmsgsrqv1TestCase.aggregate,
            bankmsgsrqv1=msgsets.Bankmsgsrqv1TestCase.aggregate,
            creditcardmsgsrqv1=msgsets.Creditcardmsgsrqv1TestCase.aggregate,
            invstmtmsgsrqv1=msgsets.Invstmtmsgsrqv1TestCase.aggregate,
            interxfermsgsrqv1=msgsets.Interxfermsgsrqv1TestCase.aggregate,
            wirexfermsgsrqv1=msgsets.Wirexfermsgsrqv1TestCase.aggregate,
            emailmsgsrqv1=msgsets.Emailmsgsrqv1TestCase.aggregate,
            seclistmsgsrqv1=msgsets.Seclistmsgsrqv1TestCase.aggregate,
            profmsgsrqv1=msgsets.Profmsgsrqv1TestCase.aggregate,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for signonmsgs, optionalmsgs in [
            (
                signonmsgsrqv1,
                [
                    signupmsgsrqv1,
                    bankmsgsrqv1,
                    creditcardmsgsrqv1,
                    invstmtmsgsrqv1,
                    interxfermsgsrqv1,
                    wirexfermsgsrqv1,
                    emailmsgsrqv1,
                    seclistmsgsrqv1,
                    profmsgsrqv1,
                ],
            ),
            (
                signonmsgsrsv1,
                [
                    signupmsgsrsv1,
                    bankmsgsrsv1,
                    creditcardmsgsrsv1,
                    invstmtmsgsrsv1,
                    interxfermsgsrsv1,
                    wirexfermsgsrsv1,
                    emailmsgsrsv1,
                    seclistmsgsrsv1,
                    profmsgsrsv1,
                ],
            ),
        ]:
            root = Element("OFX")
            root.append(signonmsgs)
            yield root
            for msgs in optionalmsgs:
                root.append(msgs)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        signonmsgsrqv1 = msgsets.Signonmsgsrqv1TestCase.etree
        signonmsgsrsv1 = msgsets.Signonmsgsrsv1TestCase.etree
        signupmsgsrqv1 = msgsets.Signupmsgsrqv1TestCase.etree
        signupmsgsrsv1 = msgsets.Signupmsgsrsv1TestCase.etree

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

    @property
    def root(self):
        return list(self.validSoup)[-1]

    def testUnsupported(self):
        instance = self.aggregate
        unsupported = list(instance.unsupported)
        self.assertEqual(unsupported, self.unsupported)
        for unsupp in unsupported:
            setattr(instance, unsupp, "FOOBAR")
            self.assertIsNone(getattr(instance, unsupp))

    def testRepr(self):
        #  instance = self.aggregate
        instance = Aggregate.from_etree(self.root)
        rep = repr(instance)
        rep_template = (
            "<OFX fid='{fid}' org='{org}' "
            "len(statements)={stmtlen} len(securities)={seclen}>"
        )
        # SIGNON values from test_models_signon.FiTestCase
        # DTSERVER from test_models_signon.SonrsTestCase
        # *MSGSRSV1 test cases include:
        #   2 STMTRS
        #   2 STMTENDRS
        #   1 CCSTMTRS
        #   1 CCSTMTENDRS
        #   2 INVSTMTRS
        #
        # 5 securitites each from 2 SECLISTs in
        # test_models_securities.SeclistTestCase (10 total)
        rep_values = {
            "fid": "4705",
            "org": "IBLLC-US",
            "dtserver": datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
            "stmtlen": 8,
            "seclen": 10,
        }
        self.assertEqual(rep, rep_template.format(**rep_values))

    def testPropertyAliases(self):
        # Make sure class property aliases have been defined correctly
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, OFX)
        self.assertIsInstance(instance.signon, SONRS)
        self.assertIsInstance(instance.securities, list)
        self.assertIsInstance(instance.statements, list)
        # *MSGSRSV1 test cases include:
        #   2 STMTRS
        #   2 STMTENDRS
        #   1 CCSTMTRS
        #   1 CCSTMTENDRS
        #   2 INVSTMTRS
        self.assertEqual(len(instance.statements), 8)

        for n, type_ in enumerate(
            [
                STMTRS,
                STMTRS,
                STMTENDRS,
                STMTENDRS,
                CCSTMTRS,
                CCSTMTENDRS,
                INVSTMTRS,
                INVSTMTRS,
            ]
        ):
            stmt = instance.statements[n]
            self.assertIsInstance(stmt, type_)
            # Verify *TRNRS wrapper TRNUID/CLTCOOKIE have been stapled
            # to the contained *RS
            self.assertEqual(stmt.trnuid, "DEADBEEF")
            self.assertEqual(stmt.cltcookie, "B00B135")


if __name__ == "__main__":
    unittest.main()
