# coding: utf-8
""" Unit tests for models.signon """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import STATUS
from ofxtools.models.signon import (
    FI,
    MFACHALLENGE,
    MFACHALLENGEA,
    SONRQ,
    SONRS,
    PINCHRQ,
    PINCHRS,
    PINCHTRNRQ,
    PINCHTRNRS,
    CHALLENGERQ,
    CHALLENGERS,
    CHALLENGETRNRQ,
    CHALLENGETRNRS,
    MFACHALLENGERQ,
    MFACHALLENGERS,
    MFACHALLENGETRNRQ,
    MFACHALLENGETRNRS,
)
from ofxtools.models.i18n import LANG_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base


class FiTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ["FID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("FI")
        SubElement(root, "ORG").text = "IBLLC-US"
        SubElement(root, "FID").text = "4705"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return FI(org="IBLLC-US", fid="4705")


class MfachallengeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MFAPHRASEID"]
    optionalElements = ["MFAPHRASELABEL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MFACHALLENGE")
        SubElement(root, "MFAPHRASEID").text = "MFA13"
        SubElement(
            root, "MFAPHRASELABEL"
        ).text = "Please enter the last four digits of your social security number"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFACHALLENGE(
            mfaphraseid="MFA13",
            mfaphraselabel="Please enter the last four digits of your social security number",
        )


class MfachallengeaTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MFAPHRASEID", "MFAPHRASEA"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MFACHALLENGEA")
        SubElement(root, "MFAPHRASEID").text = "MFA13"
        SubElement(root, "MFAPHRASEA").text = "1234"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFACHALLENGEA(mfaphraseid="MFA13", mfaphrasea="1234")


class SonrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTCLIENT", "LANGUAGE", "APPID", "APPVER"]
    optionalElements = [
        "FI",
        "GENUSERKEY",
        "SESSCOOKIE",
        "APPKEY",
        "CLIENTUID",
        "USERCRED1",
        "USERCRED2",
        "AUTHTOKEN",
        "ACCESSKEY",
    ]
    oneOfs = {"LANGUAGE": LANG_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SONRQ")
        SubElement(root, "DTCLIENT").text = "20051029101003.000[+0:UTC]"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        SubElement(root, "GENUSERKEY").text = "N"
        SubElement(root, "LANGUAGE").text = "ENG"
        root.append(FiTestCase.etree)
        SubElement(root, "SESSCOOKIE").text = "BADA55"
        SubElement(root, "APPID").text = "QWIN"
        SubElement(root, "APPVER").text = "1500"
        SubElement(root, "APPKEY").text = "CAFEBABE"
        SubElement(root, "CLIENTUID").text = "DEADBEEF"
        SubElement(root, "USERCRED1").text = "Something"
        SubElement(root, "USERCRED2").text = "Something else"
        SubElement(root, "AUTHTOKEN").text = "line noise"
        SubElement(root, "ACCESSKEY").text = "CAFEBABE"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SONRQ(
            dtclient=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
            userkey="DEADBEEF",
            genuserkey=False,
            language="ENG",
            fi=FiTestCase.aggregate,
            sesscookie="BADA55",
            appid="QWIN",
            appver="1500",
            appkey="CAFEBABE",
            clientuid="DEADBEEF",
            usercred1="Something",
            usercred2="Something else",
            authtoken="line noise",
            accesskey="CAFEBABE",
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        dtclient = Element("DTCLIENT")
        dtclient.text = "20060912"
        language = Element("LANGUAGE")
        language.text = "ENG"
        appid = Element("APPID")
        appid.text = "QWIN"
        appver = Element("APPVER")
        appver.text = "1500"

        #  "Either <USERID> and <USERPASS> or <USERKEY>, but not both"
        root = Element("SONRQ")
        root.append(dtclient)
        SubElement(root, "USERID").text = "malellolikejallello"
        SubElement(root, "USERPASS").text = "t0ps3kr1t"
        for child in language, appid, appver:
            root.append(child)
        yield root

        root = Element("SONRQ")
        root.append(dtclient)
        SubElement(root, "USERKEY").text = "DEADBEEF"
        for child in language, appid, appver:
            root.append(child)
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        dtclient = Element("DTCLIENT")
        dtclient.text = "20060912"
        language = Element("LANGUAGE")
        language.text = "ENG"
        appid = Element("APPID")
        appid.text = "QWIN"
        appver = Element("APPVER")
        appver.text = "1500"

        #  "Either <USERID> and <USERPASS> or <USERKEY>, but not both"
        root = Element("SONRQ")
        root.append(dtclient)
        for child in language, appid, appver:
            root.append(child)
        yield root

        root = Element("SONRQ")
        root.append(dtclient)
        SubElement(root, "USERID").text = "malellolikejallello"
        SubElement(root, "USERPASS").text = "t0ps3kr1t"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        for child in language, appid, appver:
            root.append(child)
        yield root


class SonrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["STATUS", "DTSERVER"]
    optionalElements = [
        "USERKEY",
        "TSKEYEXPIRE",
        "DTPROFUP",
        "DTACCTUP",
        "FI",
        "SESSCOOKIE",
        "ACCESSKEY",
    ]
    oneOfs = {"LANGUAGE": LANG_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SONRS")
        root.append(base.StatusTestCase.etree)
        SubElement(root, "DTSERVER").text = "20051029101003.000[+0:UTC]"
        SubElement(root, "USERKEY").text = "DEADBEEF"
        SubElement(root, "TSKEYEXPIRE").text = "20051231000000.000[+0:UTC]"
        SubElement(root, "LANGUAGE").text = "ENG"
        SubElement(root, "DTPROFUP").text = "20050101000000.000[+0:UTC]"
        SubElement(root, "DTACCTUP").text = "20050102000000.000[+0:UTC]"
        root.append(FiTestCase.etree)
        SubElement(root, "SESSCOOKIE").text = "BADA55"
        SubElement(root, "ACCESSKEY").text = "CAFEBABE"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SONRS(
            status=base.StatusTestCase.aggregate,
            dtserver=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
            userkey="DEADBEEF",
            tskeyexpire=datetime(2005, 12, 31, tzinfo=UTC),
            language="ENG",
            dtprofup=datetime(2005, 1, 1, tzinfo=UTC),
            dtacctup=datetime(2005, 1, 2, tzinfo=UTC),
            fi=FiTestCase.aggregate,
            sesscookie="BADA55",
            accesskey="CAFEBABE",
        )

    def testConvertRemoveProprietaryTag(cls):
        # Make sure SONRS.from_etree() removes proprietary tags
        root = deepcopy(cls.etree)
        SubElement(root, "INTU.BANKID").text = "12345678"

        sonrs = Aggregate.from_etree(root)
        cls.assertIsInstance(sonrs, SONRS)
        # Converted Aggregate should still have 10 values, not 11
        cls.assertEqual(len(sonrs._spec_repr), 10)

        cls.assertIsInstance(sonrs.status, STATUS)
        cls.assertEqual(sonrs.dtserver, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))
        cls.assertEqual(sonrs.userkey, "DEADBEEF")
        cls.assertEqual(sonrs.tskeyexpire, datetime(2005, 12, 31, tzinfo=UTC))
        cls.assertEqual(sonrs.language, "ENG")
        cls.assertEqual(sonrs.dtprofup, datetime(2005, 1, 1, tzinfo=UTC))
        cls.assertEqual(sonrs.dtacctup, datetime(2005, 1, 2, tzinfo=UTC))
        cls.assertIsInstance(sonrs.fi, FI)
        cls.assertEqual(sonrs.sesscookie, "BADA55")
        cls.assertEqual(sonrs.accesskey, "CAFEBABE")

    def testPropertyAliases(cls):
        root = Aggregate.from_etree(cls.etree)
        cls.assertEqual(root.org, "IBLLC-US")
        cls.assertEqual(root.fid, "4705")


class PinchrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["USERID", "NEWUSERPASS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PINCHRQ")
        SubElement(root, "USERID").text = "12345"
        SubElement(root, "NEWUSERPASS").text = "5321"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PINCHRQ(userid="12345", newuserpass="5321")


class PinchrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["USERID"]
    optionalElements = ["DTCHANGED"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PINCHRS")
        SubElement(root, "USERID").text = "12345"
        SubElement(root, "DTCHANGED").text = "20110101000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PINCHRS(userid="12345", dtchanged=datetime(2011, 1, 1, tzinfo=UTC))


class PinchtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PinchrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PINCHTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            pinchrq=PinchrqTestCase.aggregate,
        )


class PinchtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PinchrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PINCHTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            pinchrs=PinchrsTestCase.aggregate,
        )


class ChallengerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["USERID"]
    optionalElements = ["FICERTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CHALLENGERQ")
        SubElement(root, "USERID").text = "12345"
        SubElement(root, "FICERTID").text = "5321"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHALLENGERQ(userid="12345", ficertid="5321")


class ChallengersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["USERID", "NONCE", "FICERTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CHALLENGERS")
        SubElement(root, "USERID").text = "12345"
        SubElement(root, "NONCE").text = "REALLYRANDOM"
        SubElement(root, "FICERTID").text = "5321"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHALLENGERS(userid="12345", nonce="REALLYRANDOM", ficertid="5321")


class ChallengetrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = ChallengerqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHALLENGETRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            challengerq=ChallengerqTestCase.aggregate,
        )


class ChallengetrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ChallengersTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CHALLENGETRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            challengers=ChallengersTestCase.aggregate,
        )


class MfachallengerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTCLIENT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MFACHALLENGERQ")
        SubElement(root, "DTCLIENT").text = "20100317000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFACHALLENGERQ(dtclient=datetime(2010, 3, 17, tzinfo=UTC))


class MfachallengersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MFACHALLENGERS")
        root.append(MfachallengeTestCase.etree)
        root.append(MfachallengeTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        challenge = MfachallengeTestCase.aggregate
        return MFACHALLENGERS(challenge, challenge)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # FIXME - "1 or more"
        yield from ()


class MfachallengetrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = MfachallengerqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFACHALLENGETRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            mfachallengerq=MfachallengerqTestCase.aggregate,
        )


class MfachallengetrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = MfachallengersTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFACHALLENGETRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            mfachallengers=MfachallengersTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
