# vim: set fileencoding=utf-8

# stdlib imports
import re

# local imports
from ofxtools import Types

class OFXHeaderError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class OFXHeader(object):
    """ """
    class v1(object):
        ofxheader = Types.OneOf(100,)
        data = Types.OneOf('OFXSGML',)
        version = Types.OneOf(102, 103, 151, 160)
        security = Types.OneOf('NONE', 'TYPE1')
        encoding = Types.OneOf('USASCII','UNICODE', 'UTF-8')
        charset = Types.OneOf('ISO-8859-1', '1252', 'NONE')
        compression = Types.OneOf('NONE',)
        oldfileuid = Types.String(36)
        newfileuid = Types.String(36)

        regex = re.compile(r"""\s*
                                OFXHEADER:(?P<OFXHEADER>\d+)\s+
                                DATA:(?P<DATA>[A-Z]+)\s+
                                VERSION:(?P<VERSION>\d+)\s+
                                SECURITY:(?P<SECURITY>[\w]+)\s+
                                ENCODING:(?P<ENCODING>[A-Z]+)\s+
                                CHARSET:(?P<CHARSET>\w+)\s+
                                COMPRESSION:(?P<COMPRESSION>[A-Z]+)\s+
                                OLDFILEUID:(?P<OLDFILEUID>[\w-]+)\s+
                                NEWFILEUID:(?P<NEWFILEUID>[\w-]+)\s+
                                """, re.VERBOSE)

        def __init__(self, version, ofxheader=None, data=None, security=None,
                     encoding=None, charset=None, compression=None,
                     oldfileuid=None, newfileuid=None):
            try:
                self.ofxheader = int(ofxheader or 100)
                self.data = data or 'OFXSGML'
                self.version = int(version)
                self.security = security or 'NONE'
                self.encoding = encoding or 'USASCII'
                self.charset = charset or 'NONE'
                self.compression = compression or 'NONE'
                self.oldfileuid = oldfileuid or 'NONE'
                self.newfileuid = newfileuid or 'NONE'
            except ValueError as e:
                raise OFXHeaderError('Invalid OFX header - %s' % e.args[0])

        def __str__(self):
            # Flat text header
            fields = (  ('OFXHEADER', str(self.ofxheader)),
                      ('DATA', self.data),
                      ('VERSION', str(self.version)),
                      ('SECURITY', self.security),
                      ('ENCODING', self.encoding),
                      ('CHARSET', self.charset),
                      ('COMPRESSION', self.compression),
                      ('OLDFILEUID', self.oldfileuid),
                      ('NEWFILEUID', self.newfileuid),
                     )
            lines = [':'.join(field) for field in fields]
            lines = '\r\n'.join(lines)
            lines += '\r\n'*2
            return lines

    class v2(object):
        xmlversion = Types.OneOf('1.0',)
        encoding = Types.OneOf('UTF-8',)
        standalone = Types.OneOf('no',)
        ofxheader = Types.OneOf(200,)
        version = Types.OneOf(200, 201, 202, 203, 210, 211, 220)
        security = Types.OneOf('NONE', 'TYPE1')
        oldfileuid = Types.String(36)
        newfileuid = Types.String(36)

        regex = re.compile(r"""(<\?xml\s+
                           (version=\"(?P<XMLVERSION>[\d.]+)\")?\s*
                           (encoding=\"(?P<ENCODING>[\w-]+)\")?\s*
                           (standalone=\"(?P<STANDALONE>[\w]+)\")?\s*
                           \?>)\s*
                           <\?OFX\s+
                           OFXHEADER=\"(?P<OFXHEADER>\d+)\"\s+
                           VERSION=\"(?P<VERSION>\d+)\"\s+
                           SECURITY=\"(?P<SECURITY>[\w]+)\"\s+
                           OLDFILEUID=\"(?P<OLDFILEUID>[\w-]+)\"\s+
                           NEWFILEUID=\"(?P<NEWFILEUID>[\w-]+)\"\s*
                           \?>\s*""", re.VERBOSE)

        def __init__(self, version, xmlversion=None, encoding=None,
                     standalone=None, ofxheader=None, security=None,
                     oldfileuid=None, newfileuid=None):
            try:
                self.version = int(version)
                self.xmlversion = xmlversion or '1.0'
                self.encoding = encoding or 'UTF-8'
                self.standalone = standalone or 'no'
                self.ofxheader = int(ofxheader or 200)
                self.security = security or 'NONE'
                self.oldfileuid = oldfileuid or 'NONE'
                self.newfileuid = newfileuid or 'NONE'
            except ValueError as e:
                raise OFXHeaderError('Invalid OFX header - %s' % e.args[0])

        def __str__(self):
            # XML header
            xmlfields = (('version', self.xmlversion),
                         ('encoding', self.encoding),
                         ('standalone', self.standalone),
                        )
            xmlattrs = ['='.join((attr, '"%s"' %val)) for attr,val in xmlfields]
            xml_decl = '<?xml %s?>' % ' '.join(xmlattrs)
            fields = (('OFXHEADER', str(self.ofxheader)),
                      ('VERSION', str(self.version)),
                      ('SECURITY', self.security),
                      ('OLDFILEUID', self.oldfileuid),
                      ('NEWFILEUID', self.newfileuid),
                     )
            attrs = ['='.join((attr, '"%s"' %val)) for attr,val in fields]
            ofx_decl = '<?OFX %s?>' % ' '.join(attrs)
            return '\r\n'.join((xml_decl, ofx_decl))

    headerSpecs = {1: v1, 2: v2}

    def __init__(self, version, security=None, oldfileuid=None, 
                 newfileuid=None):
        try:
            majorVersion = int(version)//100
        except ValueError:
            raise OFXHeaderError('Invalid OFX version %s' % version)
        headerClass = self.headerSpecs[majorVersion]
        self._instance = headerClass(version=version, security=security,
                                     oldfileuid=oldfileuid,
                                     newfileuid=newfileuid
                                    )

    def __str__(self):
        return str(self._instance)

    @classmethod
    def strip(cls, source):
        # First validate OFX header
        for headerspec in cls.headerSpecs.values():
            headermatch = headerspec.regex.match(source)
            if headermatch is not None:
                headerattrs = headermatch.groupdict()
                headerattrs = {k.lower():v for k,v in headerattrs.items()}
                try:
                    header = headerspec(**headerattrs)
                except ValueError as e:
                    raise OFXHeaderError(
                        'Invalid OFX header - %s (header fields: %s)' \
                        % (e.args[0], headerattrs)
                    )
                break

        if headermatch is None:
            raise OFXHeaderError("Can't recognize OFX Header")

        # Strip OFX header and return body
        return source[headermatch.end():]
