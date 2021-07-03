# coding: utf-8
""" Unit tests for ofxtools.header """

# stdlib imports
import unittest
import uuid
from io import BytesIO
from xml.etree.ElementTree import Element
from unittest.mock import patch
from typing import Optional, Union, Mapping, Any, Type

# local imports
import ofxtools


class OFXHeaderTestMixin(object):
    # Override in subclass
    headerClass: Optional[
        Union[Type[ofxtools.header.OFXHeaderV1], Type[ofxtools.header.OFXHeaderV2]]
    ] = None
    defaultVersion: Optional[int] = None
    valid: Optional[Mapping[str, Any]] = None
    invalid: Optional[Mapping[str, Any]] = None

    body = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20051029101003</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>19991029101003</DTPROFUP>
                <DTACCTUP>20031029101003</DTACCTUP>
                <FI>
                    <ORG>NCH</ORG>
                    <FID>1001</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """.strip()

    def testValid(self):
        for attr, values in self.valid.items():
            for value in values:
                # Test class constructor with valid overrides
                kw = {attr: value}
                if attr != "version":
                    kw["version"] = self.defaultVersion
                header = self.headerClass(**kw)
                self.assertEqual(getattr(header, attr), value)

                # Test OFXHeaderBase.parse() with valid fields
                rawheader = str(header)
                (header_dupe, rest) = self.headerClass.parse(rawheader)
                for attrName, attr_ in self.headerClass.__dict__.items():
                    if hasattr(attr_, "convert"):
                        attr1 = getattr(header, attrName)
                        attr2 = getattr(header_dupe, attrName)
                        self.assertEqual(attr1, attr2)

    def testInvalid(self):
        for attr, values in self.invalid.items():
            for value in values:
                # Test class constructor with invalid overrides
                kw = {attr: value}
                if attr != "version":
                    kw["version"] = self.defaultVersion
                with self.assertRaises(ofxtools.header.OFXHeaderError):
                    self.headerClass(**kw)


class OFXHeaderV1TestCase(unittest.TestCase, OFXHeaderTestMixin):
    headerClass = ofxtools.header.OFXHeaderV1
    defaultVersion = 102
    valid = {
        "version": (102, 103, 151, 160),
        "ofxheader": (100,),
        "data": ("OFXSGML",),
        "security": ("NONE", "TYPE1"),
        "encoding": ("USASCII", "UNICODE", "UTF-8"),
        "charset": ("ISO-8859-1", "1252", "NONE"),
        "compression": ("NONE",),
        "oldfileuid": (str(uuid.uuid4()),),
        "newfileuid": (str(uuid.uuid4()),),
    }
    invalid = {
        "version": (123,),
        "ofxheader": (200,),
        "data": ("XML",),
        "security": ("TYPE2",),
        "encoding": ("UTF-16",),
        "charset": ("ISO-8859-7",),
        "compression": ("GZIP",),
        "oldfileuid": ("abc" * 36,),
        "newfileuid": ("abc" * 36,),
    }
    body_utf8 = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20051029101003</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>19991029101003</DTPROFUP>
                <DTACCTUP>20031029101003</DTACCTUP>
                <FI>
                    <ORG>漢字</ORG>
                    <FID>1001</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """.strip()
    body_cp1252 = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20051029101003</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>19991029101003</DTPROFUP>
                <DTACCTUP>20031029101003</DTACCTUP>
                <FI>
                    <ORG>Motörhead</ORG>
                    <FID>1001</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """.strip()

    def testParseHeaderDefaults(self):
        """Test parse_header() with default values for OFXv1"""
        header = str(self.headerClass(self.defaultVersion))
        ofx = header + self.body
        ofx = BytesIO(ofx.encode("ascii"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "USASCII")
        self.assertEqual(ofxheader.charset, "NONE")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)

    def testParseHeaderLatin1(self):
        """Test parse_header() with ISO-8859-1 charset"""
        header = str(
            self.headerClass(
                self.defaultVersion, encoding="UTF-8", charset="ISO-8859-1"
            )
        )
        ofx = header + self.body
        ofx = BytesIO(ofx.encode("latin_1"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "UTF-8")
        self.assertEqual(ofxheader.charset, "ISO-8859-1")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)

    def testParseHeader1252(self):
        """Test parse_header() with 1252 charset"""
        # Issue #25
        header = str(
            self.headerClass(self.defaultVersion, encoding="UTF-8", charset="1252")
        )
        ofx = header + self.body_cp1252
        ofx = BytesIO(ofx.encode("cp1252"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "UTF-8")
        self.assertEqual(ofxheader.charset, "1252")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body_cp1252)

    def testParseHeaderUnicode(self):
        """Test parse_header() with UTF-8 charset"""
        # Issue #49
        header = str(
            self.headerClass(self.defaultVersion, encoding="UTF-8", charset="NONE")
        )
        ofx = header + self.body_utf8
        ofx = BytesIO(ofx.encode("utf_8"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "UTF-8")
        self.assertEqual(ofxheader.charset, "NONE")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body_utf8)

    def testParseHeaderV1NoBlankLineBetweenHeaderAndBody(self):
        """
        Although it breaks the OFX v1 spec, we don't require an empty line
        between header and message body
        """
        header = str(self.headerClass(self.defaultVersion))
        ofx = header.strip() + "\r\n" + self.body
        ofx = BytesIO(ofx.encode("ascii"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "USASCII")
        self.assertEqual(ofxheader.charset, "NONE")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)
        # Make sure body can actually be parsed
        builder = ofxtools.Parser.TreeBuilder()
        builder.feed(body)
        root = builder.close()
        self.assertIsInstance(root, Element)
        self.assertEqual(root.tag, "OFX")
        self.assertIsNone(root.text)
        self.assertEqual(len(root), 1)

    def testParseInvalid(self):
        header = str(self.headerClass(self.defaultVersion))
        with self.assertRaises(ofxtools.header.OFXHeaderError):
            self.headerClass.parse(header[1:])

    def testStr(self):
        # Test string representation of header for version 1
        headerStr = (
            "\r\n".join(
                (
                    "OFXHEADER:100",
                    "DATA:OFXSGML",
                    "VERSION:102",
                    "SECURITY:TYPE1",
                    "ENCODING:USASCII",
                    "CHARSET:1252",
                    "COMPRESSION:NONE",
                    "OLDFILEUID:p0rkyp1g",
                    "NEWFILEUID:d0n41dduck",
                )
            )
            + "\r\n" * 2
        )
        header = self.headerClass(
            version=102,
            security="TYPE1",
            encoding="USASCII",
            charset="1252",
            oldfileuid="p0rkyp1g",
            newfileuid="d0n41dduck",
        )
        self.assertEqual(str(header), headerStr)

    def testParseHeader(self):
        # Test parse_header() for version 1
        header = str(self.headerClass(self.defaultVersion))
        ofx = header + self.body
        ofx = BytesIO(ofx.encode("utf8"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "USASCII")
        self.assertEqual(ofxheader.charset, "NONE")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)

    def testExtraWhitespaceHeaderDemarc(self):
        # Even though it breaks with the OFX spec, some FIs insert whitespace
        # after the colon demarc between an OFX header field and its value.
        # We allow this.
        header = (
            "OFXHEADER:  100\r\n"
            "DATA:  OFXSGML\r\n"
            "VERSION:  103\r\n"
            "SECURITY:  NONE\r\n"
            "ENCODING:  USASCII\r\n"
            "CHARSET:  NONE\r\n"
            "COMPRESSION:  NONE\r\n"
            "OLDFILEUID:  NONE\r\n"
            "NEWFILEUID:  NONE\r\n"
        )
        ofx = header + self.body
        ofx = BytesIO(ofx.encode("utf8"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, 103)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "USASCII")
        self.assertEqual(ofxheader.charset, "NONE")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)

    def testNoLineBreaksAnywhere(self):
        # Some FIs apparently return OFX data with no line breaks anywhere, not
        # even in the OFX header.  We're cool with that.
        #
        # Issue #89
        header = (
            "OFXHEADER:100"
            "DATA:OFXSGML"
            "VERSION:102"
            "SECURITY:NONE"
            "ENCODING:USASCII"
            "CHARSET:1252"
            "COMPRESSION:NONE"
            "OLDFILEUID:NONE"
            "NEWFILEUID:NONE"
        )
        body = (
            "<OFX><SIGNONMSGSRSV1><SONRS>"
            "<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS>"
            "<DTSERVER>20200818065106.132[-7:PDT]<LANGUAGE>ENG<FI><ORG>WF<FID>3000</FI>"
            "<SESSCOOKIE>a6a12496-682d-42b2-aafa-ed973c406a17-08182020075105922"
            "<INTU.BID>3000<INTU.USERID>jdoe</SONRS></SIGNONMSGSRSV1>"
            "<BANKMSGSRSV1><STMTTRNRS><TRNUID>0"
            "<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS>"
            "<STMTRS><CURDEF>USD<BANKACCTFROM><BANKID>121042882<ACCTID>5555555555"
            "<ACCTTYPE>CHECKING</BANKACCTFROM>"
            "<BANKTRANLIST><DTSTART>20200101120000.000[-8:PST]"
            "<DTEND>20200810110000.000[-7:PDT]"
            "<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20200403110000.000[-7:PDT]"
            "<TRNAMT>507500.00<FITID>202004031<NAME>TD AMERITRADE CLEARING"
            "<MEMO>WT SEQ555555 /ORG=JOHN DOE SRF# EC55555555555 TRN#55555555555 RFB# 55555555555"
            "</STMTTRN></BANKTRANLIST>"
            "<LEDGERBAL><BALAMT>56498.04<DTASOF>20200817110000.000[-7:PDT]</LEDGERBAL>"
            "<AVAILBAL><BALAMT>56498.04<DTASOF>20200817110000.000[-7:PDT]</AVAILBAL>"
            "</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        )
        ofx = header + body
        ofx = BytesIO(ofx.encode("utf8"))
        ofxheader, body_ = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 100)
        self.assertEqual(ofxheader.data, "OFXSGML")
        self.assertEqual(ofxheader.version, 102)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.encoding, "USASCII")
        self.assertEqual(ofxheader.charset, "1252")
        self.assertEqual(ofxheader.compression, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, body_)


class OFXHeaderV2TestCase(unittest.TestCase, OFXHeaderTestMixin):
    headerClass = ofxtools.header.OFXHeaderV2
    defaultVersion = 200
    valid = {
        "version": (200, 201, 202, 203, 210, 211, 220),
        "ofxheader": (200,),
        "security": ("NONE", "TYPE1"),
        "oldfileuid": (str(uuid.uuid4()),),
        "newfileuid": (str(uuid.uuid4()),),
    }
    invalid = {
        "version": (123,),
        "ofxheader": (100,),
        "security": ("TYPE2",),
        "oldfileuid": ("abc" * 36,),
        "newfileuid": ("abc" * 36,),
    }

    def testParseHeaderV2NoNewlineBetweenHeaderAndBody(self):
        """OFXv2 doesn't need newline between header and message body"""
        # Issue #47
        header = str(self.headerClass(self.defaultVersion))
        ofx = header.strip() + self.body
        ofx = BytesIO(ofx.encode("ascii"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 200)
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)
        # Make sure body can actually be parsed
        builder = ofxtools.Parser.TreeBuilder()
        builder.feed(body)
        root = builder.close()
        self.assertIsInstance(root, Element)
        self.assertEqual(root.tag, "OFX")
        self.assertIsNone(root.text)
        self.assertEqual(len(root), 1)

    def testParseInvalid(self):
        header = str(self.headerClass(self.defaultVersion))
        with self.assertRaises(ofxtools.header.OFXHeaderError):
            self.headerClass.parse(header.replace("?", "!"))

    def testStr(self):
        headerStr = (
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            + "\r\n"
            + "<?OFX %s?>"
            % " ".join(
                (
                    'OFXHEADER="200"',
                    'VERSION="200"',
                    'SECURITY="TYPE1"',
                    'OLDFILEUID="p0rkyp1g"',
                    'NEWFILEUID="d0n41dduck"',
                )
            )
            + "\r\n" * 2
        )
        header = self.headerClass(
            version=200,
            security="TYPE1",
            oldfileuid="p0rkyp1g",
            newfileuid="d0n41dduck",
        )
        self.assertEqual(str(header).strip(), headerStr.strip())

    def testParseHeader(self):
        # Test parse_header() for version 2
        header = str(self.headerClass(self.defaultVersion))
        ofx = header + self.body
        ofx = BytesIO(ofx.encode("utf8"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 200)
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)

    def testParseHeaderSingleQuotedDeclarationData(self):
        # The XML spec allows data to be quoted within either single or double quotes
        # Make sure that single-quoted data in the XML declaration is captured by
        # ``ofxtools.header.XML_REGEX``
        header = str(self.headerClass(self.defaultVersion))
        header = (
            "<?xml version='1.0' encoding='UTF-8' standalone='no'?>"
            + header[header.find("<?OFX") :]
        )
        ofx = header + self.body
        ofx = BytesIO(ofx.encode("utf8"))
        ofxheader, body = ofxtools.header.parse_header(ofx)

        self.assertEqual(ofxheader.ofxheader, 200)
        self.assertEqual(ofxheader.version, self.defaultVersion)
        self.assertEqual(ofxheader.security, "NONE")
        self.assertEqual(ofxheader.oldfileuid, "NONE")
        self.assertEqual(ofxheader.newfileuid, "NONE")

        self.assertEqual(body, self.body)


class MakeHeaderTestCase(unittest.TestCase):
    def testOfxV1(self):
        """
        For 100 <= version < 200, make_header() calls OFXHeaderV1 and
        passes through args.
        """
        valid_versions = (102, 103, 151, 160)
        oldfileuid = "p0rkyp1g"
        newfileuid = "d0n41dduck"
        with patch("ofxtools.header.OFXHeaderV1") as fake_OFXHeaderV1:
            for version in valid_versions:
                for security in ("NONE", "TYPE1"):
                    ofxtools.header.make_header(
                        version,
                        security=security,
                        oldfileuid=oldfileuid,
                        newfileuid=newfileuid,
                    )
                    fake_OFXHeaderV1.assert_called_with(
                        version,
                        security=security,
                        oldfileuid=oldfileuid,
                        newfileuid=newfileuid,
                    )

    def testOfxV2(self):
        """
        For 200 <= version < 300, make_header() calls OFXHeaderV2 and
        passes through args.
        """
        valid_versions = (200, 201, 202, 203, 210, 211, 220)
        oldfileuid = "p0rkyp1g"
        newfileuid = "d0n41dduck"
        with patch("ofxtools.header.OFXHeaderV2") as fake_OFXHeaderV2:
            for version in valid_versions:
                for security in ("NONE", "TYPE1"):
                    ofxtools.header.make_header(
                        version,
                        security=security,
                        oldfileuid=oldfileuid,
                        newfileuid=newfileuid,
                    )
                    fake_OFXHeaderV2.assert_called_with(
                        version,
                        security=security,
                        oldfileuid=oldfileuid,
                        newfileuid=newfileuid,
                    )

    def testInvalidVersion(self):
        with self.assertRaises(ofxtools.header.OFXHeaderError):
            ofxtools.header.make_header(0)
        with self.assertRaises(ofxtools.header.OFXHeaderError):
            ofxtools.header.make_header(301)
        with self.assertRaises(ofxtools.header.OFXHeaderError):
            ofxtools.header.make_header("horses")


if __name__ == "__main__":
    unittest.main()
