# coding: utf-8
""" Unit tests for ofxtools.Client """

# stdlib imports
import unittest
from unittest.mock import patch, DEFAULT, sentinel, ANY
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.Client import (
    OFXClient,
    StmtRq,
    CcStmtRq,
    InvStmtRq,
    StmtEndRq,
    CcStmtEndRq,
)
from ofxtools.utils import UTC


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


if __name__ == "__main__":
    unittest.main()
