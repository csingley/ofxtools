# vim: set fileencoding=utf-8
"""
Open Financial Exchange (OFX) message header, both version 1 & version 2 (XML),
which precedes the OFX message body.

See section 2.2 of the OFX spec.

The main data classes - `OFXHeaderV1` and `OFXHeaderV2` - perform validation
and type conversion; see `ofxtools.Types` for details.  Their `parse()` method
constructs class instances from strings, which is used in deserialization.

This module provides the `parse_header()` function, which demarcates message
header from message body in serialized OFX data, and processes the header
portion.  See `ofxtools.Parser` for the rest of it.

Also provided is the `make_header()` utility function, which routes to the
appropriate header class based on OFX version #.  It's used by
`ofxtools.Client`.
"""

# stdlib imports
import re


# local imports
from ofxtools import Types


class OFXHeaderError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class OFXHeaderBase:
    """
    Superclass for OFXHeader{V1,V2} factoring out common logic.
    """
    regex = NotImplemented  # Define in subclass
    codec = NotImplemented  # Define in subclass

    @classmethod
    def parse(cls, rawheader):
        """
        Instantiate from string.

        Returns a tuple of:
            * class instance containing parsed header data, and
            * index of header regex match end position (type int).
        """
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
    #  https://docs.python.org/3/library/codecs.html#standard-encodings
    codecs = {'ISO-8859-1': 'latin_1', '1252': 'cp1252', 'NONE': 'utf_8'}
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
        """
        String codec used to decode OFX message body.

        Maps from OFX character set name to Python codec name.
        """
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
        # More recent versions of the OFXv1 spec require newlines to demarcate
        # the message header from the message body
        lines += '\r\n' * 2
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
    codec = 'utf_8'

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
        return '\r\n'.join((xml_decl, ofx_decl, ''))


XML_REGEX = re.compile(r"""(<\?xml\s+
                       (version=\"(?P<xmlversion>[\d.]+)\")?\s*
                       (encoding=\"(?P<encoding>[\w-]+)\")?\s*
                       (standalone=\"(?P<standalone>[\w]+)\")?\s*
                       \?>)\s*""", re.VERBOSE)


def parse_header(source):
    """
    Consume source; feed to appropriate class constructor which performs
    validation/type conversion on OFX header.

    Using header, locate/read/decode (but do not parse) OFX data body.

    Returns a 2-tuple of:
        * instance of OFXHeaderV1/OFXHeaderV2 containing parsed data, and
        * decoded text of OFX data body
    """
    # Skip any empty lines at the beginning
    while True:
        # OFX header is read by nice clean machines, not meatbags -
        # should not contain emoji, 漢字, or what have you.
        line = source.readline().decode('ascii')
        if line.strip():
            break

    # If the first non-empty line contains an XML declaration, it's OFX v2
    xml_match = XML_REGEX.match(line)
    if xml_match:
        # OFXv2 spec doesn't require newlines between XML declaration,
        # OFX declaration, and data elements; `line` may or may not
        # contain the latter two.
        #
        # Just rewind, read the whole file (it must be UTF-8 encoded per
        # the spec) and slice the OFX data body from the end of the
        # OFX declaration
        source.seek(0)
        decoded_source = source.read().decode(OFXHeaderV2.codec)
        header, header_end_index = OFXHeaderV2.parse(decoded_source)
        message = decoded_source[header_end_index:]
    else:
        # OFX v1
        rawheader = line + '\n'
        # First line is OFXHEADER; need to read next 8 lines for a fixed
        # total of 9 fields required by OFX v1 spec.
        for n in range(8):
            rawheader += source.readline().decode('ascii')
        header, header_end_index = OFXHeaderV1.parse(rawheader)

        #  Input source stream position has advanced to the beginning of
        #  the OFX body tag soup, which is where subsequent calls
        #  to read()/readlines() will pick up.
        #
        #  Decode the OFX data body according to the encoding declared
        #  in the OFX header
        message = source.read().decode(header.codec)

    return header, message.strip()


def make_header(version, security=None, oldfileuid=None, newfileuid=None):
    """
    Route to OFXHeaderV1 / OFXHeaderV2 according to the input OFX version #,
    and return an instance of the appropriate class.

    Polymorphic convenience utility.
    """
    try:
        major_version = int(version)//100
    except ValueError:
        raise OFXHeaderError('Invalid OFX version %s' % version)
    try:
        HeaderClass = {1: OFXHeaderV1, 2: OFXHeaderV2}[major_version]
    except KeyError:
        raise OFXHeaderError('OFX version %s not version 1 or version 2'
                             % version)
    return HeaderClass(version, security=security,
                       oldfileuid=oldfileuid, newfileuid=newfileuid)
