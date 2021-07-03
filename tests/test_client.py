# coding: utf-8
""" Unit tests for ofxtools.Client """

# stdlib imports
import unittest
from unittest.mock import patch, DEFAULT, sentinel, Mock
from datetime import datetime
import xml.etree.ElementTree as ET
import socket
from io import BytesIO


# local imports
from ofxtools.Client import (
    OFXClient,
    StmtRq,
    CcStmtRq,
    InvStmtRq,
    StmtEndRq,
    CcStmtEndRq,
)
from ofxtools.models.signon import SIGNONMSGSRQV1
from ofxtools.utils import UTC, indent, tostring_unclosed_elements
from ofxtools.models.signon import SONRQ


DEFAULT_APPID = "QWIN"
DEFAULT_APPVER = "2700"


class OFXClientV1TestCase(unittest.TestCase):
    @property
    def client(self):
        client = OFXClient(
            "https://example.com/ofx",
            userid="elmerfudd",
            org="FIORG",
            fid="FID",
            version=103,
            bankid="123456789",
            brokerid="example.com",
            persist_cookies=False,  # TESTME - need to test `persist_cookies`=True
        )
        # Mock out OFXClient._get_service_urls(), which hits the Internet.
        client._get_service_urls = Mock(
            return_value={StmtRq: "https://example.com/ofx"}
        )
        return client

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
        client = OFXClient("http://example.com", userid="porkypig")
        with patch("ofxtools.Client.OFXClient.dtclient") as mock_dtclient:
            mock_dtclient.return_value = datetime(2017, 4, 1, tzinfo=UTC)
            signon = client.signon("t0ps3kr1t")
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

    def testSignonVersion102(self):
        # CLIENTUID wasn't defined until OFX version 1.0.3,
        # so it returns None if if initialized.
        client = OFXClient(
            "http://example.com", userid="porkypig", clientuid="DEADBEEF", version=102
        )
        signon = client.signon("t0ps3kr1t")
        self.assertIsInstance(signon, SIGNONMSGSRQV1)
        signon = signon.sonrq
        self.assertIsNone(signon.clientuid)

    def testRequestStatementsDryrun(self):
        with patch.multiple(
            "ofxtools.Client.OFXClient", dtclient=DEFAULT, uuid="DEADBEEF"
        ) as mock:
            mock["dtclient"].return_value = datetime(2017, 4, 1, tzinfo=UTC)

            dryrun = (
                self.client.request_statements("t0ps3kr1t", self.stmtRq0, dryrun=True)
                .read()
                .decode()
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
                "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
                "<USERID>elmerfudd</USERID>"
                "<USERPASS>t0ps3kr1t</USERPASS>"
                "<LANGUAGE>ENG</LANGUAGE>"
                "<FI>"
                "<ORG>FIORG</ORG>"
                "<FID>FID</FID>"
                "</FI>"
                "<APPID>{appid}</APPID>"
                "<APPVER>{appver}</APPVER>"
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
                "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
                "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
                "<INCLUDE>Y</INCLUDE>"
                "</INCTRAN>"
                "</STMTRQ>"
                "</STMTTRNRQ>"
                "</BANKMSGSRQV1>"
                "</OFX>"
            ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)
            self.assertEqual(dryrun, request)

    def _testRequest(self, fn, *args, **kwargs):
        """Mock out the relevant parts of ``urllib`` that get called by
        ``ofxtools.Client.OFXClient.download()``, then call the function
        with the given arguments.

        Return the serialized data passed to ``urllib.request.Request`` by
        ``ofxtools.Client.OFXClient.download()`` (as a string, not bytes)
        """
        with patch.multiple(
            "urllib.request", Request=DEFAULT, urlopen=DEFAULT
        ) as mock_urllib:
            with patch("uuid.uuid4") as mock_uuid:
                with patch("ofxtools.Client.OFXClient.dtclient") as mock_dtclient:
                    # Mock out DTCLIENT/CLIENTUID to get static values, not dynamic
                    mock_dtclient.return_value = datetime(2017, 4, 1, tzinfo=UTC)
                    mock_uuid.return_value = "DEADBEEF"
                    # Mock out urllib.request's Request that gets called by
                    # OFXClient.download()
                    mock_Request = mock_urllib["Request"]
                    mock_Request.return_value = sentinel.REQUEST
                    # Mock out the url_opener that gets called by
                    # OFXClient.download() for the case of `persist_cookies=False`
                    mock_urlopen = mock_urllib["urlopen"]
                    mock_urlopen.return_value = BytesIO(b"Some OFX Response")
                    # Mock out the url_opener that gets called by
                    # OFXClient.download() for the case of `persist_cookies=True`
                    # FIXME

                    # With the necessary mocks in place, call the function with
                    # the given arguments.
                    output = fn(*args, **kwargs)

                    # OFXClient.download() calls Request with these args:
                    #  self.url, method="POST", data=request, headers=self.http_headers
                    rq_args = mock_Request.call_args[0]

                    self.assertEqual(len(rq_args), 1)
                    self.assertEqual(rq_args[0], self.client.url)

                    rq_kwargs = mock_Request.call_args[1]
                    self.assertEqual(rq_kwargs["method"], "POST")
                    self.assertEqual(rq_kwargs["headers"], self.client.http_headers)

                    # OFXClient.download() calls urlopen() with these args:
                    #  req, timeout=timeout
                    mock_urlopen.assert_called_once_with(
                        sentinel.REQUEST,
                        timeout=10.0,
                    )

                    # The tested function should return the output of download(),
                    # which itself returns the output of urlopen()
                    self.assertEqual(output.read(), b"Some OFX Response")

                    return rq_kwargs["data"].decode("utf_8")

    def testRequestStatements(self):
        data = self._testRequest(
            self.client.request_statements, "t0ps3kr1t", self.stmtRq0
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
            "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>{appid}</APPID>"
            "<APPVER>{appver}</APPVER>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "</BANKMSGSRQV1>"
            "</OFX>"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    def testRequestStatementsEmpty(self):
        data = self._testRequest(self.client.request_statements, "t0ps3kr1t")

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
            "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>{appid}</APPID>"
            "<APPVER>{appver}</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "</OFX>"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    def testRequestStatementsMultipleMixed(self):
        data = self._testRequest(
            self.client.request_statements,
            "t0ps3kr1t",
            self.stmtRq0,
            self.stmtRq1,
            self.ccStmtRq,
            self.invStmtRq,
            self.stmtEndRq,
            self.ccStmtEndRq,
        )

        self.maxDiff = None

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
            "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>{appid}</APPID>"
            "<APPVER>{appver}</APPVER>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
            "</STMTENDRQ>"
            "</STMTENDTRNRQ>"
            "<STMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<STMTRQ>"
            "<BANKACCTFROM>"
            "<BANKID>123456789</BANKID>"
            "<ACCTID>111111</ACCTID>"
            "<ACCTTYPE>CHECKING</ACCTTYPE>"
            "</BANKACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
            "<INCLUDE>Y</INCLUDE>"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "</BANKMSGSRQV1>"
            "<CREDITCARDMSGSRQV1>"
            "<CCSTMTENDTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<CCSTMTENDRQ>"
            "<CCACCTFROM>"
            "<ACCTID>222222</ACCTID>"
            "</CCACCTFROM>"
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
            "</CCSTMTENDRQ>"
            "</CCSTMTENDTRNRQ>"
            "<CCSTMTTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<CCSTMTRQ>"
            "<CCACCTFROM>"
            "<ACCTID>333333</ACCTID>"
            "</CCACCTFROM>"
            "<INCTRAN>"
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
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
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    def testRequestStatementsPrettyprint(self):
        client = OFXClient(
            "https://example.com/ofx",
            userid="elmerfudd",
            org="FIORG",
            fid="FID",
            version=103,
            prettyprint=True,
            bankid="123456789",
            brokerid="example.com",
            persist_cookies=False,
        )
        # Mock out OFXClient._get_service_urls(), which hits the Internet.
        client._get_service_urls = Mock(
            return_value={StmtRq: "https://example.com/ofx"}
        )
        data = self._testRequest(client.request_statements, "t0ps3kr1t", self.stmtRq0)

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
            "      <DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>\n"
            "      <USERID>elmerfudd</USERID>\n"
            "      <USERPASS>t0ps3kr1t</USERPASS>\n"
            "      <LANGUAGE>ENG</LANGUAGE>\n"
            "      <FI>\n"
            "        <ORG>FIORG</ORG>\n"
            "        <FID>FID</FID>\n"
            "      </FI>\n"
            "      <APPID>{appid}</APPID>\n"
            "      <APPVER>{appver}</APPVER>\n"
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
            "          <DTSTART>20170101000000.000[+0:UTC]</DTSTART>\n"
            "          <DTEND>20170331000000.000[+0:UTC]</DTEND>\n"
            "          <INCLUDE>Y</INCLUDE>\n"
            "        </INCTRAN>\n"
            "      </STMTRQ>\n"
            "    </STMTTRNRQ>\n"
            "  </BANKMSGSRQV1>\n"
            "</OFX>\n"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    def testRequestStatementsUnclosedTags(self):
        client = OFXClient(
            "https://example.com/ofx",
            userid="elmerfudd",
            org="FIORG",
            fid="FID",
            version=103,
            close_elements=False,
            bankid="123456789",
            brokerid="example.com",
            persist_cookies=False,
        )
        # Mock out OFXClient._get_service_urls(), which hits the Internet.
        client._get_service_urls = Mock(
            return_value={StmtRq: "https://example.com/ofx"}
        )
        data = self._testRequest(client.request_statements, "t0ps3kr1t", self.stmtRq0)

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
            "<DTCLIENT>20170401000000.000[+0:UTC]"
            "<USERID>elmerfudd"
            "<USERPASS>t0ps3kr1t"
            "<LANGUAGE>ENG"
            "<FI>"
            "<ORG>FIORG"
            "<FID>FID"
            "</FI>"
            "<APPID>{appid}"
            "<APPVER>{appver}"
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
            "<DTSTART>20170101000000.000[+0:UTC]"
            "<DTEND>20170331000000.000[+0:UTC]"
            "<INCLUDE>Y"
            "</INCTRAN>"
            "</STMTRQ>"
            "</STMTTRNRQ>"
            "</BANKMSGSRQV1>"
            "</OFX>"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    def testRequestStatementsUnclosedTagsOFXv2(self):
        # OFX version 2 (XML) doesn't allow unclosed tags.
        # This is already checked by OFXClient.__init__(), so to test this
        # illegal state we have to be sneaky and change the attribute after
        # instantiation
        client = OFXClient(
            "https://example.com/ofx",
            userid="elmerfudd",
            org="FIORG",
            fid="FID",
            version=203,
            close_elements=True,
            bankid="123456789",
            brokerid="example.com",
        )
        client.close_elements = False
        with self.assertRaises(ValueError):
            self._testRequest(client.request_statements, "t0ps3kr1t", self.stmtRq0)

    def testRequestStatementsBadRequestType(self):
        # OFXClient.request_statements() pukes if you don't feed it one of the
        # special-purpose *STMTRQ/*STMTENDRQ NamedTuple instances
        with self.assertRaises(ValueError):
            self._testRequest(
                self.client.request_statements, "t0ps3kr1t", "I SHOULD BE A STMTRQ"
            )

    def testRequestEndStatements(self):
        data = self._testRequest(
            self.client.request_statements, "t0ps3kr1t", self.stmtEndRq
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
            "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>{appid}</APPID>"
            "<APPVER>{appver}</APPVER>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
            "</STMTENDRQ>"
            "</STMTENDTRNRQ>"
            "</BANKMSGSRQV1>"
            "</OFX>"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    def testRequestEndStatementsMultipleMixed(self):
        data = self._testRequest(
            self.client.request_statements,
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
            "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>{appid}</APPID>"
            "<APPVER>{appver}</APPVER>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
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
            "<DTSTART>20170101000000.000[+0:UTC]</DTSTART>"
            "<DTEND>20170331000000.000[+0:UTC]</DTEND>"
            "</CCSTMTENDRQ>"
            "</CCSTMTENDTRNRQ>"
            "</CREDITCARDMSGSRQV1>"
            "</OFX>"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)

    # FIXME - this is going to be more difficult to test; we need to mock
    # out quite a bit of stuff to shortcut the disk caching and request parsing.
    #  def testRequestProfile(self):
    #      client = OFXClient(
    #          "https://example.com/ofx",
    #          org="FIORG",
    #          fid="FID",
    #          version=103,
    #          bankid="123456789",
    #          brokerid="example.com",
    #          persist_cookies=False,
    #      )
    #      data = self._testRequest(client.request_profile)

    #      request = (
    #          "OFXHEADER:100\r\n"
    #          "DATA:OFXSGML\r\n"
    #          "VERSION:103\r\n"
    #          "SECURITY:NONE\r\n"
    #          "ENCODING:USASCII\r\n"
    #          "CHARSET:NONE\r\n"
    #          "COMPRESSION:NONE\r\n"
    #          "OLDFILEUID:NONE\r\n"
    #          "NEWFILEUID:DEADBEEF\r\n"
    #          "\r\n"
    #          "<OFX>"
    #          "<SIGNONMSGSRQV1>"
    #          "<SONRQ>"
    #          "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
    #          "<USERID>anonymous00000000000000000000000</USERID>"
    #          "<USERPASS>anonymous00000000000000000000000</USERPASS>"
    #          "<LANGUAGE>ENG</LANGUAGE>"
    #          "<FI>"
    #          "<ORG>FIORG</ORG>"
    #          "<FID>FID</FID>"
    #          "</FI>"
    #          "<APPID>{appid}</APPID>"
    #          "<APPVER>{appver}</APPVER>"
    #          "</SONRQ>"
    #          "</SIGNONMSGSRQV1>"
    #          "<PROFMSGSRQV1>"
    #          "<PROFTRNRQ>"
    #          "<TRNUID>DEADBEEF</TRNUID>"
    #          "<PROFRQ>"
    #          "<CLIENTROUTING>NONE</CLIENTROUTING>"
    #          "<DTPROFUP>19900101000000.000[+0:UTC]</DTPROFUP>"
    #          "</PROFRQ>"
    #          "</PROFTRNRQ>"
    #          "</PROFMSGSRQV1>"
    #          "</OFX>"
    #      ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

    #      self.assertEqual(data, request)

    def testRequestAccounts(self):
        data = self._testRequest(
            self.client.request_accounts,
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
            "<DTCLIENT>20170401000000.000[+0:UTC]</DTCLIENT>"
            "<USERID>elmerfudd</USERID>"
            "<USERPASS>t0ps3kr1t</USERPASS>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<FI>"
            "<ORG>FIORG</ORG>"
            "<FID>FID</FID>"
            "</FI>"
            "<APPID>{appid}</APPID>"
            "<APPVER>{appver}</APPVER>"
            "</SONRQ>"
            "</SIGNONMSGSRQV1>"
            "<SIGNUPMSGSRQV1>"
            "<ACCTINFOTRNRQ>"
            "<TRNUID>DEADBEEF</TRNUID>"
            "<ACCTINFORQ>"
            "<DTACCTUP>19541031000000.000[+0:UTC]</DTACCTUP>"
            "</ACCTINFORQ>"
            "</ACCTINFOTRNRQ>"
            "</SIGNUPMSGSRQV1>"
            "</OFX>"
        ).format(appid=DEFAULT_APPID, appver=DEFAULT_APPVER)

        self.assertEqual(data, request)


class OFXClientV2TestCase(unittest.TestCase):
    def testUnclosedTagsOFXv2(self):
        """OFXv2 (XML) doesn't support unclosed tags"""
        with self.assertRaises(ValueError):
            OFXClient(
                "https://example.com/ofx",
                userid="elmerfudd",
                org="FIORG",
                fid="FID",
                version=203,
                close_elements=False,
                bankid="123456789",
                brokerid="example.com",
            )


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
        self.assertEqual(
            result,
            (
                "<ROOT>\n"
                "  <LEVEL1>\n"
                "    <LEVEL2>level2</LEVEL2>\n"
                "  </LEVEL1>\n"
                "  <LEVEL1 />\n"
                "</ROOT>\n"
            ),
        )

    def testTostringUnclosedElements(self):
        result = tostring_unclosed_elements(self.root).decode()
        self.assertEqual(
            result,
            ("<ROOT>" "<LEVEL1>" "<LEVEL2>level2" "</LEVEL1>" "<LEVEL1>" "</ROOT>"),
        )


if __name__ == "__main__":
    unittest.main()
