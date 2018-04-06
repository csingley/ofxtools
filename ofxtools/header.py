# vim: set fileencoding=utf-8

# stdlib imports
import re


# local imports
from ofxtools import Types


class OFXHeaderError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class OFXHeader(object):
    """
    OFX header wrapper.

    Class constructors [i.e. __init__() and convert()] route to
    OFXHeaderV1 / OFXHeaderV2 according to the input OFX version number,
    and return an instance of the appropriate class.
    """
    xmldeclregex = re.compile(r"""(<\?xml\s+
                              (version=\"(?P<xmlversion>[\d.]+)\")?\s*
                              (encoding=\"(?P<encoding>[\w-]+)\")?\s*
                              (standalone=\"(?P<standalone>[\w]+)\")?\s*
                              \?>)\s*""", re.VERBOSE)

    @classmethod
    def parse(cls, source):
        """
        Consume source thru end of OFX header; feed to appropriate class
        constructor which performs validation/type conversion on OFX header.

        Returns instance of OFXHeaderV1/OFXHeaderV2 containing parsed data.

        As a side effect, input source stream position is advanced to the
        beginning of the OFX body tag soup, which is where subsequent calls
        to read()/readlines() will pick up.
        """
        # Skip any empty lines at the beginning
        while True:
            line = source.readline().decode('ascii')
            if line.strip():
                break

        # If the first non-empty line is an XML declaration, it's OFX v2
        xmldeclmatch = cls.xmldeclregex.match(line)
        if xmldeclmatch:
            headerclass = OFXHeaderV2
            # First line is XML declaration; OFX header is next line
            rawheader = source.readline().decode('ascii')
        else:
            # OFX v1
            headerclass = OFXHeaderV1
            rawheader = line + '\n'
            # First line is OFXHEADER; need to read next 8 lines for a fixed
            # total of 9 fields required by OFX v1 spec.
            for n in range(8):
                rawheader += source.readline().decode('ascii')

        headermatch = headerclass.regex.match(rawheader)
        if not headermatch:
            msg = 'OFX header is malformed: {}'.format(rawheader)
            raise OFXHeaderError(msg)
        headerattrs = headermatch.groupdict()
        headerattrs = {k.lower(): v for k, v in headerattrs.items()}
        header = headerclass(**headerattrs)
        return header

    def __init__(self, version, security=None, oldfileuid=None,
                 newfileuid=None):
        """
        Pass input args to OFXHeaderV1/OFXHeaderV2; store returned instance
        as self._instance
        """
        try:
            major_version = int(version)//100
        except ValueError:
            raise OFXHeaderError('Invalid OFX version %s' % version)
        HeaderClass = {1: OFXHeaderV1, 2: OFXHeaderV2}[major_version]
        self._instance = HeaderClass(version=version, security=security,
                                     oldfileuid=oldfileuid,
                                     newfileuid=newfileuid)

    def __str__(self):
        return str(self._instance)


class OFXHeaderV1(object):
    """ Header for OFX version 1 """
    ofxheader = Types.OneOf(100,)
    data = Types.OneOf('OFXSGML',)
    version = Types.OneOf(102, 103, 151, 160)
    security = Types.OneOf('NONE', 'TYPE1')
    encoding = Types.OneOf('USASCII', 'UNICODE', 'UTF-8')
    # DRY - mapping of CHARSET: codec used below in codec()
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

    @property
    def codec(self):
        return self.codecs[self.charset]

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
        except ValueError as err:
            raise OFXHeaderError('Invalid OFX header - %s' % err.args[0])

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


class OFXHeaderV2(object):
    """ Header for OFX version 2 """
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
    # UTF-8 encoding required by OFXv2 spec; explicitly listed here to
    # conform to v1 class interface above.
    codec = 'utf8'

    def __init__(self, version, ofxheader=None, security=None,
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
