# coding: utf-8
""" Unit tests for ofxtools.Client """

# stdlib imports
import unittest
from unittest.mock import MagicMock, patch, DEFAULT, sentinel, ANY
from datetime import datetime
from collections import namedtuple
from io import BytesIO
import xml.etree.ElementTree as ET
import argparse


# local imports
from ofxtools.Client import (
    OFXClient,
    StmtRq,
    CcStmtRq,
    InvStmtRq,
    StmtEndRq,
    CcStmtEndRq,
    indent,
    tostring_unclosed_elements,
    OFXConfigParser,
    init_client,
    make_argparser,
    merge_config,
    do_stmt,
    do_profile,
)
from ofxtools.utils import UTC
from ofxtools.models.signon import SIGNONMSGSRQV1, SONRQ


class OFXClientV1TestCase(unittest.TestCase):
    @property
    def client(self):
        return OFXClient(
            "https://example.com/ofx",
            org="FIORG",
            fid="FID",
            version=103,
            bankid="123456789",
            brokerid="example.com",
        )

    @property
    def stmtRq0(self):
        return StmtRq(
            acctid="111111",
            accttype="CHECKING",
            dtstart=datetime(2017, 1, 1, tzinfo=UTC),
            dtend=datetime(2017, 3, 31, tzinfo=UTC),
        )

    @property
    def stmtRq1(self):
        return StmtRq(
            acctid="222222",
            accttype="SAVINGS",
            dtstart=datetime(2017, 1, 1, tzinfo=UTC),
            dtend=datetime(2017, 3, 31, tzinfo=UTC),
        )

    @property
    def ccStmtRq(self):
        return CcStmtRq(
            acctid="333333",
            dtstart=datetime(2017, 1, 1, tzinfo=UTC),
            dtend=datetime(2017, 3, 31, tzinfo=UTC),
        )

    @property
    def invStmtRq(self):
        return InvStmtRq(
            acctid="444444",
            dtstart=datetime(2017, 1, 1, tzinfo=UTC),
            dtend=datetime(2017, 3, 31, tzinfo=UTC),
        )

    @property
    def stmtEndRq(self):
        return StmtEndRq(
            acctid="111111",
            accttype="CHECKING",
            dtstart=datetime(2017, 1, 1, tzinfo=UTC),
            dtend=datetime(2017, 3, 31, tzinfo=UTC),
        )

    @property
    def ccStmtEndRq(self):
        return CcStmtEndRq(
            acctid="222222",
            dtstart=datetime(2017, 1, 1, tzinfo=UTC),
            dtend=datetime(2017, 3, 31, tzinfo=UTC),
        )

    def testDtclient(self):
        now = datetime.now(UTC)
        then = self.client.dtclient()
        self.assertIsInstance(then, datetime)
        self.assertLess((then - now).seconds, 1)

    def testSignonEmptyFIORG(self):
        client = OFXClient("http://example.com")
        with patch("ofxtools.Client.OFXClient.dtclient") as mock_dtclient:
            mock_dtclient.return_value = datetime(2017, 4, 1, tzinfo=UTC)
            signon = client.signon("porkypig", "t0ps3kr1t")
            self.assertIsInstance(signon, SIGNONMSGSRQV1)
            signon = signon.sonrq
            self.assertIsInstance(signon, SONRQ)
            self.assertEqual(signon.dtclient, datetime(2017, 4, 1, tzinfo=UTC))
            self.assertEqual(signon.userid, "porkypig")
            self.assertEqual(signon.userpass, "t0ps3kr1t")
            self.assertEqual(signon.language, "ENG")
            self.assertIsNone(signon.fi)
            self.assertIsNone(signon.sesscookie)
            self.assertEqual(signon.appid, client.appid)
            self.assertEqual(signon.appver, client.appver)
            self.assertIsNone(signon.clientuid)

    def testRequestStatementsDryrun(self):
        with patch("uuid.uuid4") as mock_uuid:
            with patch("ofxtools.Client.OFXClient.dtclient") as mock_dtclient:
                mock_dtclient.return_value = datetime(2017, 4, 1, tzinfo=UTC)
                mock_uuid.return_value = "DEADBEEF"

                dryrun = self.client.request_statements(
                    "elmerfudd", "t0ps3kr1t", self.stmtRq0, dryrun=True
                ).read().decode()
                request = (
                    "OFXHEADER:100\r\n"
                    "DATA:OFXSGML\r\n"
                    "VERSION:103\r\n"
                    "SECURITY:NONE\r\n"
                    "ENCODING:USASCII\r\n"
                    "CHARSET:NONE\r\n"
                    "COMPRESSION:NONE\r\n"
                    "OLDFILEUID:NONE\r\n"
                    "NEWFILEUID:DEADBEEF\r\n"
                    "\r\n"
                    "<OFX>"
                    "<SIGNONMSGSRQV1>"
                    "<SONRQ>"
                    "<DTCLIENT>20170401000000</DTCLIENT>"
                    "<USERID>elmerfudd</USERID>"
                    "<USERPASS>t0ps3kr1t</USERPASS>"
                    "<LANGUAGE>ENG</LANGUAGE>"
                    "<FI>"
                    "<ORG>FIORG</ORG>"
                    "<FID>FID</FID>"
                    "</FI>"
                    "<APPID>QWIN</APPID>"
                    "<APPVER>2300</APPVER>"
                    "</SONRQ>"
                    "</SIGNONMSGSRQV1>"
                    "<BANKMSGSRQV1>"
                    "<STMTTRNRQ>"
                    "<TRNUID>DEADBEEF</TRNUID>"
                    "<STMTRQ>"
                    "<BANKACCTFROM>"
                    "<BANKID>123456789</BANKID>"
                    "<ACCTID>111111</ACCTID>"
                    "<ACCTTYPE>CHECKING</ACCTTYPE>"
                    "</BANKACCTFROM>"
                    "<INCTRAN>"
                    "<DTSTART>20170101000000</DTSTART>"
                    "<DTEND>20170331000000</DTEND>"
                    "<INCLUDE>Y</INCLUDE>"
                    "</INCTRAN>"
                    "</STMTRQ>"
                    "</STMTTRNRQ>"
                    "</BANKMSGSRQV1>"
                    "</OFX>"
                )
                self.assertEqual(dryrun, request)

    def _testRequest(self, fn, *args, **kwargs):
        with patch.multiple(
            "urllib.request", Request=DEFAULT, urlopen=DEFAULT
        ) as mock_urllib:
            with patch("uuid.uuid4") as mock_uuid:
                with patch("ofxtools.Client.OFXClient.dtclient") as mock_dtclient:
                    mock_dtclient.return_value = datetime(2017, 4, 1, tzinfo=UTC)
                    mock_uuid.return_value = "DEADBEEF"
                    mock_Request = mock_urllib["Request"]
                    mock_Request.return_value = sentinel.REQUEST
                    mock_urlopen = mock_urllib["urlopen"]
                    mock_urlopen.return_value = sentinel.RESPONSE
                    output = fn(*args, **kwargs)

                    args = mock_Request.call_args[0]
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], self.client.url)

                    kwargs = mock_Request.call_args[1]
                    self.assertEqual(kwargs["method"], "POST")
                    self.assertEqual(kwargs["headers"], self.client.http_headers)

                    mock_urlopen.assert_called_once_with(sentinel.REQUEST, context=ANY)
                    self.assertEqual(output, sentinel.RESPONSE)

                    return kwargs["data"].decode("utf_8")

    def testRequestStatements(self):
        data = self._testRequest(
            self.client.request_statements, "elmerfudd", "t0ps3kr1t", self.stmtRq0
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<BANKMSGSRQV1>"
            "<STMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<STMTRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789</BANKID>"
            "<ACCTID>111111</ACCTID>"
            "<ACCTTYPE>CHECKING</ACCTTYPE>"
            "</BANKACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "</BANKMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestStatementsEmpty(self):
        data = self._testRequest(
            self.client.request_statements, "elmerfudd", "t0ps3kr1t"
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestStatementsBadArgs(self):
        with self.assertRaises(ValueError):
            self._testRequest(
                self.client.request_statements, "elmerfudd", "t0ps3kr1t", self.stmtEndRq
            )

    def testRequestStatementsMultipleMixed(self):
        data = self._testRequest(
            self.client.request_statements,
            "elmerfudd",
            "t0ps3kr1t",
            self.stmtRq0,
            self.stmtRq1,
            self.ccStmtRq,
            self.invStmtRq,
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<BANKMSGSRQV1>"
            "<STMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<STMTRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789</BANKID>"
            "<ACCTID>111111</ACCTID>"
            "<ACCTTYPE>CHECKING</ACCTTYPE>"
            "</BANKACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "<STMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<STMTRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789</BANKID>"
            "<ACCTID>222222</ACCTID>"
            "<ACCTTYPE>SAVINGS</ACCTTYPE>"
            "</BANKACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "</BANKMSGSRQV1>"
            "<CREDITCARDMSGSRQV1>"
            "<CCSTMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<CCSTMTRQ>"
            "<CCACCTFROM>"
            "<ACCTID>333333</ACCTID>"
            "</CCACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "</CCSTMTRQ>"
            "</CCSTMTTRNRQ>"
            "</CREDITCARDMSGSRQV1>"
            "<INVSTMTMSGSRQV1>"
            "<INVSTMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<INVSTMTRQ>"
            "<INVACCTFROM>"
            "<BROKERID>example.com</BROKERID>"
            "<ACCTID>444444</ACCTID>"
            "</INVACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "<INCOO>N</INCOO>"
            "<INCPOS>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCPOS>"
            "<INCBAL>Y</INCBAL>"
            "</INVSTMTRQ>"
            "</INVSTMTTRNRQ>"
            "</INVSTMTMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestStatementsPrettyprint(self):
        data = self._testRequest(
            self.client.request_statements, "elmerfudd", "t0ps3kr1t", self.stmtRq0, prettyprint=True
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>\n"
            "  <SIGNONMSGSRQV1>\n"
            "    <SONRQ>\n"
            "      <DTCLIENT>20170401000000</DTCLIENT>\n"
            "      <USERID>elmerfudd</USERID>\n"
            "      <USERPASS>t0ps3kr1t</USERPASS>\n"
            "      <LANGUAGE>ENG</LANGUAGE>\n"
            "      <FI>\n"
            "        <ORG>FIORG</ORG>\n"
            "        <FID>FID</FID>\n"
            "      </FI>\n"
            "      <APPID>QWIN</APPID>\n"
            "      <APPVER>2300</APPVER>\n"
            "    </SONRQ>\n"
            "  </SIGNONMSGSRQV1>\n"
            "  <BANKMSGSRQV1>\n"
            "    <STMTTRNRQ>\n"
            "      <TRNUID>DEADBEEF</TRNUID>\n"
            "      <STMTRQ>\n"
            "        <BANKACCTFROM>\n"
            "          <BANKID>123456789</BANKID>\n"
            "          <ACCTID>111111</ACCTID>\n"
            "          <ACCTTYPE>CHECKING</ACCTTYPE>\n"
            "        </BANKACCTFROM>\n"
            "        <INCTRAN>\n"
            "          <DTSTART>20170101000000</DTSTART>\n"
            "          <DTEND>20170331000000</DTEND>\n"
            "          <INCLUDE>Y</INCLUDE>\n"
            "        </INCTRAN>\n"
            "      </STMTRQ>\n"
            "    </STMTTRNRQ>\n"
            "  </BANKMSGSRQV1>\n"
            "</OFX>\n"
        )

        self.assertEqual(data, request)

    def testRequestStatementsUnclosedTags(self):
        data = self._testRequest(
            self.client.request_statements,
            "elmerfudd",
            "t0ps3kr1t",
            self.stmtRq0,
            close_elements=False,
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000"
            "<USERID>elmerfudd"
            "<USERPASS>t0ps3kr1t"
            "<LANGUAGE>ENG"
            "<FI>"
            "<ORG>FIORG"
            "<FID>FID"
            "</FI>"
            "<APPID>QWIN"
            "<APPVER>2300"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<BANKMSGSRQV1>"
            "<STMTTRNRQ>"
            "<TRNUID>DEADBEEF"
            "<STMTRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789"
            "<ACCTID>111111"
            "<ACCTTYPE>CHECKING"
            "</BANKACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000"
            "<DTEND>20170331000000"
            "<INCLUDE>Y"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "</BANKMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestStatementsUnclosedTagsOFXv2(self):
        """ OFXv2 (XML) doesn't support unclosed tags """
        client = self.client
        client.version = 203
        with self.assertRaises(ValueError):
            self._testRequest(
                client.request_statements,
                "elmerfudd",
                "t0ps3kr1t",
                self.stmtRq0,
                close_elements=False,
            )

    def testRequestEndStatements(self):
        data = self._testRequest(
            self.client.request_end_statements, "elmerfudd", "t0ps3kr1t", self.stmtEndRq
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<BANKMSGSRQV1>"
            "<STMTENDTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<STMTENDRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789</BANKID>"
            "<ACCTID>111111</ACCTID>"
            "<ACCTTYPE>CHECKING</ACCTTYPE>"
            "</BANKACCTFROM>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "</STMTENDRQ>"
            "</STMTENDTRNRQ>"
            "</BANKMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestEndStatementsBadArgs(self):
        with self.assertRaises(ValueError):
            self._testRequest(
                self.client.request_end_statements, "elmerfudd", "t0ps3kr1t", self.stmtRq0
            )

    def testRequestEndStatementsMultipleMixed(self):
        data = self._testRequest(
            self.client.request_end_statements,
            "elmerfudd",
            "t0ps3kr1t",
            self.stmtEndRq,
            self.ccStmtEndRq,
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<BANKMSGSRQV1>"
            "<STMTENDTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<STMTENDRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789</BANKID>"
            "<ACCTID>111111</ACCTID>"
            "<ACCTTYPE>CHECKING</ACCTTYPE>"
            "</BANKACCTFROM>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "</STMTENDRQ>"
            "</STMTENDTRNRQ>"
            "</BANKMSGSRQV1>"
            "<CREDITCARDMSGSRQV1>"
            "<CCSTMTENDTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<CCSTMTENDRQ>"
            "<CCACCTFROM>"
            "<ACCTID>222222</ACCTID>"
            "</CCACCTFROM>"
            "<DTSTART>20170101000000</DTSTART>"
            "<DTEND>20170331000000</DTEND>"
            "</CCSTMTENDRQ>"
            "</CCSTMTENDTRNRQ>"
            "</CREDITCARDMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestEndStatementsEmpty(self):
        data = self._testRequest(
            self.client.request_end_statements, "elmerfudd", "t0ps3kr1t"
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestProfile(self):
        data = self._testRequest(self.client.request_profile)

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>anonymous00000000000000000000000</USERID>"
            "<USERPASS>anonymous00000000000000000000000</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<PROFMSGSRQV1>"
            "<PROFTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<PROFRQ>"
            "<CLIENTROUTING>NONE</CLIENTROUTING>"
            "<DTPROFUP>19900101000000</DTPROFUP>"
            "</PROFRQ>"
            "</PROFTRNRQ>"
            "</PROFMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)

    def testRequestAccounts(self):
        data = self._testRequest(
            self.client.request_accounts,
            "elmerfudd",
            "t0ps3kr1t",
            datetime(1954, 10, 31, tzinfo=UTC),
        )

        request = (
            "OFXHEADER:100\r\n"
            "DATA:OFXSGML\r\n"
            "VERSION:103\r\n"
            "SECURITY:NONE\r\n"
            "ENCODING:USASCII\r\n"
            "CHARSET:NONE\r\n"
            "COMPRESSION:NONE\r\n"
            "OLDFILEUID:NONE\r\n"
            "NEWFILEUID:DEADBEEF\r\n"
            "\r\n"
            "<OFX>"
            "<SIGNONMSGSRQV1>"
            "<SONRQ>"
            "<DTCLIENT>20170401000000</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>QWIN</APPID>"
            "<APPVER>2300</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<SIGNUPMSGSRQV1>"
            "<ACCTINFOTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<ACCTINFORQ>"
            "<DTACCTUP>19541031000000</DTACCTUP>"
            "</ACCTINFORQ>"
            "</ACCTINFOTRNRQ>"
            "</SIGNUPMSGSRQV1>"
            "</OFX>"
        )

        self.assertEqual(data, request)


class UtilitiesTestCase(unittest.TestCase):
    @property
    def root(self):
        root = ET.Element("ROOT")
        level1 = ET.SubElement(root, "LEVEL1")
        ET.SubElement(level1, "LEVEL2").text = "level2"
        ET.SubElement(root, "LEVEL1")
        return root

    def testIndent(self):
        root = self.root
        indent(root)
        result = ET.tostring(root).decode()
        self.assertEqual(result, ("<ROOT>\n"
                                  "  <LEVEL1>\n"
                                  "    <LEVEL2>level2</LEVEL2>\n"
                                  "  </LEVEL1>\n"
                                  "  <LEVEL1 />\n"
                                  "</ROOT>\n"))

    def testTostringUnclosedElements(self):
        result = tostring_unclosed_elements(self.root).decode()
        self.assertEqual(result, ("<ROOT>"
                                  "<LEVEL1>"
                                  "<LEVEL2>level2"
                                  "</LEVEL1>"
                                  "<LEVEL1>"
                                  "</ROOT>"))


class OFXConfigParserTestCase(unittest.TestCase):
    @property
    def parser(self):
        parser = OFXConfigParser()
        return parser

    def testRead(self):
        with patch("configparser.ConfigParser.read") as fake_read:
            filenames = ["/fake/path"]
            self.parser.read(filenames)
            args, kwargs = fake_read.call_args
            self.assertEqual(len(args), 2)
            parser = args[0]
            self.assertIsInstance(parser, OFXConfigParser)
            self.assertEqual(args[1], filenames)
            self.assertEqual(len(kwargs), 0)

    def testFiIndex(self):
        pass


class CliTestCase(unittest.TestCase):
    @property
    def args(self):
        return argparse.Namespace(
            url="http://example.com",
            org="Example",
            fid="666",
            version="103",
            appid="ofxtools",
            appver="0.7.0",
            language="ENG",
            bankid="1234567890",
            brokerid="example.com",
            dtstart="20070101000000",
            dtend="20071231000000",
            dtasof="20071231000000",
            checking=["123", "234"],
            savings=["345", "456"],
            moneymrkt=["567", "678"],
            creditline=["789", "890"],
            creditcard=["111", "222"],
            investment=["333", "444"],
            inctran=True,
            incoo=False,
            incpos=True,
            incbal=True,
            dryrun=True,
            user="porkypig",
            clientuid=None,
            unclosedelements=False)

    def testInitClient(self):
        args = self.args
        client = init_client(args)
        self.assertIsInstance(client, OFXClient)
        self.assertEqual(str(client.version), args.version)
        for arg in ['url', 'org', 'fid', 'appid', 'appver', 'language',
                    'bankid', 'brokerid']:
            self.assertEqual(getattr(client, arg), getattr(args, arg))

    def testDoStmt(self):
        args = self.args
        args.dryrun = False

        with patch('getpass.getpass') as fake_getpass:
            fake_getpass.return_value = "t0ps3kr1t"
            with patch('ofxtools.Client.OFXClient.request_statements') as fake_rq_stmt:
                fake_rq_stmt.return_value = BytesIO(b"th-th-th-that's all folks!")
                output = do_stmt(args)

                self.assertEqual(output, None)

                args, kwargs = fake_rq_stmt.call_args
                user, password, *stmtrqs = args
                self.assertEqual(user, "porkypig")
                self.assertEqual(password, "t0ps3kr1t")
                self.assertEqual(stmtrqs, [
                    StmtRq(acctid="123", accttype="CHECKING", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="234", accttype="CHECKING", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="345", accttype="SAVINGS", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="456", accttype="SAVINGS", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="567", accttype="MONEYMRKT", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="678", accttype="MONEYMRKT", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="789", accttype="CREDITLINE", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    StmtRq(acctid="890", accttype="CREDITLINE", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    CcStmtRq(acctid="111", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    CcStmtRq(acctid="222", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                    InvStmtRq(acctid="333", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), dtasof=datetime(2007, 12, 31, tzinfo=UTC), inctran=True, incoo=False, incpos=True, incbal=True),
                    InvStmtRq(acctid="444", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), dtasof=datetime(2007, 12, 31, tzinfo=UTC), inctran=True, incoo=False, incpos=True, incbal=True),
                ])
                self.assertEqual(kwargs, {'clientuid': None, 'dryrun': False, 'close_elements': True})

    def testDoStmtDryrun(self):
        with patch('ofxtools.Client.OFXClient.request_statements') as fake_rq_stmt:
            fake_rq_stmt.return_value = BytesIO(b"th-th-th-that's all folks!")
            output = do_stmt(self.args)

            self.assertEqual(output, None)

            args, kwargs = fake_rq_stmt.call_args
            user, password, *stmtrqs = args
            self.assertEqual(user, "porkypig")
            self.assertEqual(password, "{:0<32}".format("anonymous"))
            self.assertEqual(stmtrqs, [
                StmtRq(acctid="123", accttype="CHECKING", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="234", accttype="CHECKING", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="345", accttype="SAVINGS", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="456", accttype="SAVINGS", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="567", accttype="MONEYMRKT", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="678", accttype="MONEYMRKT", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="789", accttype="CREDITLINE", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                StmtRq(acctid="890", accttype="CREDITLINE", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                CcStmtRq(acctid="111", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                CcStmtRq(acctid="222", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), inctran=True),
                InvStmtRq(acctid="333", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), dtasof=datetime(2007, 12, 31, tzinfo=UTC), inctran=True, incoo=False, incpos=True, incbal=True),
                InvStmtRq(acctid="444", dtstart=datetime(2007, 1, 1, tzinfo=UTC), dtend=datetime(2007, 12, 31, tzinfo=UTC), dtasof=datetime(2007, 12, 31, tzinfo=UTC), inctran=True, incoo=False, incpos=True, incbal=True),
            ])
            self.assertEqual(kwargs, {'clientuid': None, 'dryrun': True, 'close_elements': True})

    def testDoProfile(self):
        with patch('ofxtools.Client.OFXClient.request_profile') as fake_rq_prof:
            fake_rq_prof.return_value = BytesIO(b"th-th-th-that's all folks!")

            output = do_profile(self.args)

            self.assertEqual(output, None)

            args, kwargs = fake_rq_prof.call_args
            self.assertEqual(len(args), 0)
            self.assertEqual(kwargs, {'dryrun': True, 'close_elements': True})


class MainTestCase(unittest.TestCase):
    @property
    def args(self):
        return argparse.Namespace(
            server="2big2fail",
            dtstart="20070101000000",
            dtend="20071231000000",
            dtasof="20071231000000",
            checking=[],
            savings=["444"],
            moneymrkt=[],
            creditline=[],
            creditcard=["555"],
            investment=["666"],
            inctran=True,
            incoo=False,
            incpos=True,
            incbal=True,
            dryrun=True,
            user=None,
            clientuid=None,
            unclosedelements=False)

    def testMakeArgparser(self):
        fi_index = ['bank0', 'broker0']
        argparser = make_argparser(fi_index)
        self.assertEqual(len(argparser._actions), 28)

    def testMergeConfig(self):
        config = MagicMock()
        config.fi_index = ["2big2fail"]
        self.assertEqual(config.fi_index, ["2big2fail"])
        config.items.return_value = [("user", "porkypig"), ("checking", "111"), ("creditcard", "222, 333")]

        args = merge_config(config, self.args)
        self.assertIsInstance(args, argparse.Namespace)
        # Only the args specified in config.items() have been updated
        for attr in (
            "server", "dtstart", "dtend", "dtasof", "savings", "moneymrkt",
            "creditline", "investment", "inctran", "incoo", "incpos", "incbal",
            "dryrun", "clientuid", "unclosedelements"):
            self.assertEqual(getattr(args, attr), getattr(self.args, attr))
        self.assertEqual(args.user, "porkypig")
        self.assertEqual(args.checking, ["111"])
        self.assertEqual(args.savings, ["444"])
        # CLI args override config completely (not append)
        self.assertEqual(args.creditcard, ["555"])

    def testMergeConfigUnknownFiArg(self):
        config = MagicMock()
        config.fi_index = []
        with self.assertRaises(ValueError):
            merge_config(config, self.args)


if __name__ == "__main__":
    unittest.main()
