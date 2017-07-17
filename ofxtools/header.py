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
        version = Types.OneOf(102, 151, 160)
        security = Types.OneOf('NONE', 'TYPE1')
        encoding = Types.OneOf('USASCII', 'UNICODE', 'UTF-8')
        codecs = {'ISO-8859-1': 'latin1', '1252': 'cp1252', 'NONE': 'utf8'}
        charset = Types.OneOf(*codecs.keys())
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

        @property
        def codec(self):
            return self.codecs[self.charset]

        def __str__(self):
            # Flat text header
            fields = (('OFXHEADER', str(self.ofxheader)),
                      ('DATA', self.data),
                      ('VERSION', str(self.version)),
                      ('SECURITY', self.security),
                      ('ENCODING', self.encoding),
                      ('CHARSET', self.charset),
                      ('COMPRESSION', self.compression),
                      ('OLDFILEUID', self.oldfileuid),
                      ('NEWFILEUID', self.newfileuid),)
            lines = [':'.join(field) for field in fields]
            lines = '\r\n'.join(lines)
            lines += '\r\n'*2
            return lines

    class v2(object):
        ofxheader = Types.OneOf(200,)
        version = Types.OneOf(200, 201, 202, 203, 210, 211, 220)
        security = Types.OneOf('NONE', 'TYPE1')
        oldfileuid = Types.String(36)
        newfileuid = Types.String(36)

        regex = re.compile(r"""<\?OFX\s+
                           OFXHEADER=\"(?P<ofxheader>\d+)\"\s+
                           VERSION=\"(?P<version>\d+)\"\s+
                           SECURITY=\"(?P<security>[\w]+)\"\s+
                           OLDFILEUID=\"(?P<oldfileuid>[\w-]+)\"\s+
                           NEWFILEUID=\"(?P<newfileuid>[\w-]+)\"\s*
                           \?>\s*""", re.VERBOSE)

        codec = 'utf8'

        def __init__(self, version, xmlversion=None, encoding=None,
                     standalone=None, ofxheader=None, security=None,
                     oldfileuid=None, newfileuid=None):
            try:
                self.version = int(version)
                self.ofxheader = int(ofxheader or 200)
                self.security = security or 'NONE'
                self.oldfileuid = oldfileuid or 'NONE'
                self.newfileuid = newfileuid or 'NONE'
            except ValueError as e:
                raise OFXHeaderError('Invalid OFX header - %s' % e.args[0])

        def __str__(self):
            # XML header
            xml_decl = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            fields = (('OFXHEADER', str(self.ofxheader)),
                      ('VERSION', str(self.version)),
                      ('SECURITY', self.security),
                      ('OLDFILEUID', self.oldfileuid),
                      ('NEWFILEUID', self.newfileuid),)
            attrs = ['='.join((attr, '"%s"' % val)) for attr, val in fields]
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
                                     newfileuid=newfileuid)

    def __str__(self):
        return str(self._instance)

    xmldeclregex = re.compile(r"""(<\?xml\s+
                              (version=\"(?P<xmlversion>[\d.]+)\")?\s*
                              (encoding=\"(?P<encoding>[\w-]+)\")?\s*
                              (standalone=\"(?P<standalone>[\w]+)\")?\s*
                              \?>)\s*""", re.VERBOSE)

    @classmethod
    def parse(cls, source):
        # Skip any blank lines at the beginning
        while True:
            ln = cls.readline(source)
            if ln:
                break

        xmldeclmatch = cls.xmldeclregex.match(ln)
        if xmldeclmatch:
            # OFX v2
            headerclass = cls.v2
            # First line is XML declaration; OFX header is next line
            rawheader = cls.readline(source)
        else:
            # OFX v1
            headerclass = cls.v1
            if 'OFXHEADER' not in ln:
                msg = 'OFX header not declared: {}'.format(ln)
                raise OFXHeaderError(msg)
            rawheader = ln + '\n'
            for n in range(8):
                rawheader += cls.readline(source, strip=False)

        headermatch = headerclass.regex.match(rawheader)
        if not headermatch:
            msg = 'OFX header is malformed: {}'.format(rawheader)
            raise OFXHeaderError(msg)
        headerattrs = headermatch.groupdict()
        headerattrs = {k.lower(): v for k, v in headerattrs.items()}
        header = headerclass(**headerattrs)
        return header

    @staticmethod
    def readline(source, strip=True):
        ln = source.readline().decode('ascii')
        if strip:
            ln = ln.strip()
        return ln
