# coding: utf-8
""" Unit tests for models.profile """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.profile import (
    PROFRQ,
    PROFRS,
    PROFTRNRQ,
    PROFTRNRS,
    SIGNONINFO,
    SIGNONINFOLIST,
    MSGSETLIST,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base


class ProfrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CLIENTROUTING", "DTPROFUP"]
    oneOfs = {"CLIENTROUTING": ("NONE", "SERVICE", "MSGSET")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFRQ")
        SubElement(root, "CLIENTROUTING").text = "SERVICE"
        SubElement(root, "DTPROFUP").text = "20010401000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFRQ(
            clientrouting="SERVICE", dtprofup=datetime(2001, 4, 1, tzinfo=UTC)
        )


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

    oneOfs = {
        "CHARTYPE": ("ALPHAONLY", "NUMERICONLY", "ALPHAORNUMERIC", "ALPHAANDNUMERIC")
    }

    @classproperty
    @classmethod
    def etree(cls):
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

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONINFO(
            signonrealm="AMERITRADE",
            min=4,
            max=32,
            chartype="ALPHAORNUMERIC",
            casesen=True,
            special=False,
            spaces=False,
            pinch=False,
            chgpinfirst=False,
        )
        #  usercred1label='What is your name?',
        #  usercred2label='What is your favorite color?',
        #  clientuidreq=False,
        #  authtokenfirst=True,
        #  authtokenlabel='Enigma',
        #  authtokeninfourl='http://www.google.com',
        #  mfachallengesupt=False,
        #  mfachallengefirst=True,
        #  accesstokenreq=False,


class SignoninfolistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SIGNONINFOLIST")
        for i in range(2):
            #  for i in range(1):
            signoninfo = SignoninfoTestCase.etree
            root.append(signoninfo)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SIGNONINFOLIST(
            SignoninfoTestCase.aggregate, SignoninfoTestCase.aggregate
        )


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

    @classproperty
    @classmethod
    def msgsetlist(cls):
        # Manually define MSGSETLIST here, to avoid circular import
        # from test_models_msgsets
        root = Element("MSGSETLIST")
        signonmsgset = SubElement(root, "SIGNONMSGSET")
        signonmsgsetv1 = SubElement(signonmsgset, "SIGNONMSGSETV1")
        msgsetcore = SubElement(signonmsgsetv1, "MSGSETCORE")
        SubElement(msgsetcore, "VER").text = "1"
        SubElement(
            msgsetcore, "URL"
        ).text = "https://ofxs.ameritrade.com/cgi-bin/apps/OFX"
        SubElement(msgsetcore, "OFXSEC").text = "NONE"
        SubElement(msgsetcore, "TRANSPSEC").text = "Y"
        SubElement(msgsetcore, "SIGNONREALM").text = "AMERITRADE"
        SubElement(msgsetcore, "LANGUAGE").text = "ENG"
        SubElement(msgsetcore, "SYNCMODE").text = "FULL"
        SubElement(msgsetcore, "REFRESHSUPT").text = "N"
        SubElement(msgsetcore, "RESPFILEER").text = "N"
        #  SubElement(msgsetcore, "INTU.TIMEOUT").text = "360"
        SubElement(msgsetcore, "SPNAME").text = "Dewey Cheatham & Howe"
        return root

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PROFRS")
        root.append(cls.msgsetlist)
        root.append(SignoninfolistTestCase.etree)
        SubElement(root, "DTPROFUP").text = "20010401000000.000[+0:UTC]"
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

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFRS(
            msgsetlist=Aggregate.from_etree(cls.msgsetlist),
            signoninfolist=SignoninfolistTestCase.aggregate,
            dtprofup=datetime(2001, 4, 1, tzinfo=UTC),
            finame="Dewey Cheatham & Howe",
            addr1="3717 N Clark St",
            addr2="Dugout Box, Aisle 19",
            addr3="Seat A1",
            city="Chicago",
            state="IL",
            postalcode="60613",
            country="USA",
            csphone="(773) 309-1027",
            tsphone="(773) 309-1028",
            faxphone="(773) 309-1029",
            url="http://www.ameritrade.com",
            email="support@ameritrade.com",
        )

    def testConvertRemoveProprietaryTag(self):
        # Make sure SONRS.from_etree() removes proprietary tags
        root = self.etree
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

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            profrq=ProfrqTestCase.aggregate,
        )


class ProftrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = ProfrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PROFTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            profrs=ProfrsTestCase.aggregate,
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        profile = instance.profile
        self.assertIsInstance(profile, PROFRS)


if __name__ == "__main__":
    unittest.main()
