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
        Consume source; feed to appropriate class constructor which performs
        validation/type conversion on OFX header.

        Using header, locate/read/decode (but do not parse) OFX data body.

        Returns a tuple of:
            * instance of OFXHeaderV1/OFXHeaderV2 containing parsed data, and
            * decoded text of OFX data body
        """
        # Skip any empty lines at the beginning
        while True:
            line = source.readline().decode('ascii')
            if line.strip():
                break

        # If the first non-empty line has an XML declaration, it's OFX v2
        xmldeclmatch = cls.xmldeclregex.match(line)
        if xmldeclmatch:
            # OFXv2 spec doesn't require newlines between XML declaration,
            # OFX declaration, and data elements; `line` may or may not
            # contain the latter two.
            #
            # Just rewind, read the whole file (it must be UTF-8 encoded per
            # the spec) and slice the OFX data body from the end of the
            # OFX declaration
            source.seek(0)
            whole_thing = source.read().decode(OFXHeaderV2.codec)
            header, end = OFXHeaderV2.parse(whole_thing)
            ofx = whole_thing[end:]
        else:
            # OFX v1
            rawheader = line + '\n'
            # First line is OFXHEADER; need to read next 8 lines for a fixed
            # total of 9 fields required by OFX v1 spec.
            for n in range(8):
                rawheader += source.readline().decode('ascii')
            header, end = OFXHeaderV1.parse(rawheader)

            #  Input source stream position has advanced to the beginning of
            #  the OFX body tag soup, which is where subsequent calls
            #  to read()/readlines() will pick up.
            #
            #  Decode the OFX data body according to the encoding declared
            #  in the OFX header
            ofx = source.read().decode(header.codec)

        return header, ofx.strip()

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


class OFXHeaderBase:
    """
    Superclass for OFXHeader{V1,V2}
    """
    @classmethod
    def parse(cls, rawheader):
        headermatch = cls.regex.search(rawheader)
        if not headermatch:
            msg = 'OFX header is malformed:\n{}'.format(rawheader)
            raise OFXHeaderError(msg)
        headerattrs = headermatch.groupdict()
        headerattrs = {k.lower(): v for k, v in headerattrs.items()}
        header = cls(**headerattrs)
        return header, headermatch.end()


class OFXHeaderV1(OFXHeaderBase):
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
                            ENCODING:(?P<ENCODING>[A-Z0-9-]+)\s+
                            CHARSET:(?P<CHARSET>[\w-]+)\s+
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


class OFXHeaderV2(OFXHeaderBase):
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
