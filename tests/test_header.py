# vim: set fileencoding=utf-8

# stdlib imports
import unittest
import uuid


# local imports
import ofxtools


class OFXHeaderTestMixin(object):
    """ """
    # Override in subclass
    headerClass = None
    defaultVersion = None
    valid = None
    invalid = None

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
                kw = {attr: value}
                if attr != 'version':
                    kw['version']=self.defaultVersion
                header = self.headerClass(**kw)
                self.assertEqual(getattr(header, attr), value)

    def testInvalid(self):
        for attr, values in self.invalid.items():
            for value in values:
                kw = {attr: value}
                if attr != 'version':
                    kw['version']=self.defaultVersion
                with self.assertRaises(ofxtools.header.OFXHeaderError):
                    header = self.headerClass(**kw)

    def testStrip(self):
        header = str(self.headerClass(self.defaultVersion))
        ofx = header + self.body
        body = ofxtools.header.OFXHeader.strip(ofx)
        self.assertEqual(body, self.body)


class OFXHeaderV1TestCase(unittest.TestCase, OFXHeaderTestMixin):
    headerClass = ofxtools.header.OFXHeader.v1
    defaultVersion = 102
    valid = {'version': (102, 103, 151, 160),
             'ofxheader': (100,),
             'data': ('OFXSGML',),
             'security': ('NONE', 'TYPE1'),
             'encoding': ('USASCII', 'UNICODE', 'UTF-8'),
             'charset': ('ISO-8859-1', '1252', 'NONE'),
             'compression': ('NONE',),
             'oldfileuid': (str(uuid.uuid4()),),
             'newfileuid': (str(uuid.uuid4()),),
            }
    invalid = {'version': (123,),
               'ofxheader': (200,),
               'data': ('XML',),
               'security': ('TYPE2',),
               'encoding': ('UTF-16',),
               'charset': ('ISO-8859-7',),
               'compression': ('GZIP',),
               'oldfileuid': ('abc'*36,),
               'newfileuid': ('abc'*36,),
              }

    def testStr(self):
        headerStr = '\r\n'.join((
            'OFXHEADER:100',
            'DATA:OFXSGML',
            'VERSION:102',
            'SECURITY:TYPE1',
            'ENCODING:USASCII',
            'CHARSET:1252',
            'COMPRESSION:NONE',
            'OLDFILEUID:p0rkyp1g',
            'NEWFILEUID:d0n41dduck',
        )) + '\r\n'*2
        header = self.headerClass(version=102, security='TYPE1',
                                  encoding='USASCII', charset='1252',
                                  oldfileuid='p0rkyp1g',
                                  newfileuid='d0n41dduck')
        self.assertEqual(str(header), headerStr)


class OFXHeaderV2TestCase(unittest.TestCase, OFXHeaderTestMixin):
    headerClass = ofxtools.header.OFXHeader.v2
    defaultVersion = 200
    valid = {'version': (200, 201, 202, 203, 210, 211, 220),
             'xmlversion': ('1.0',),
             'encoding': ('UTF-8',),
             'standalone': ('no',),
             'ofxheader': (200,),
             'security': ('NONE', 'TYPE1'),
             'oldfileuid': (str(uuid.uuid4()),),
             'newfileuid': (str(uuid.uuid4()),),
            }
    invalid = {'version': (123,),
               'xmlversion': ('2.0',),
               'encoding': ('UTF-16',),
               'standalone': ('yes',),
               'ofxheader': (100,),
               'security': ('TYPE2',),
               'oldfileuid': ('abc'*36,),
               'newfileuid': ('abc'*36,),
              }

    def testStr(self):
        headerStr = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' \
                + '\r\n' \
                + '<?OFX %s?>' % ' '.join((
                    'OFXHEADER="200"',
                    'VERSION="200"',
                    'SECURITY="TYPE1"',
                    'OLDFILEUID="p0rkyp1g"',
                    'NEWFILEUID="d0n41dduck"',
        )) + '\r\n'*2
        header = self.headerClass(version=200, security='TYPE1',
                                  oldfileuid='p0rkyp1g',
                                  newfileuid='d0n41dduck')
        self.assertEqual(str(header).strip(), headerStr.strip())


if __name__=='__main__':
    unittest.main()
