# vim: set fileencoding=utf-8

# stdlib imports
import unittest


# 3rd party imports
import ofxtools

sgml = """
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


class HeaderV1TestCase(unittest.TestCase):
    header = """
    OFXHEADER:100
    DATA:OFXSGML
    VERSION:102
    SECURITY:NONE
    ENCODING:USASCII
    CHARSET:1252
    COMPRESSION:NONE
    OLDFILEUID:NONE
    NEWFILEUID:NONE
    """.strip()

    @property
    def ofx(self):
        return self.header + '\n\n' + sgml

    def test_header(self):
        body = ofxtools.header.OFXHeader.strip(self.ofx)
        self.assertEqual(body, sgml)


class HeaderV2TestCase(HeaderV1TestCase):
    header = """
    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <?OFX OFXHEADER="200" VERSION="200" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>
    """.strip()
