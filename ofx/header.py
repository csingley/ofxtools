# vim: set fileencoding=utf-8

# stdlib imports
import re


class OFXHeaderError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class OFXHeader(object):
    """ """
    class v1(object):
        regex = re.compile(r"""\s*
                                OFXHEADER:(?P<OFXHEADER>\d+)\s+
                                DATA:(?P<DATA>[A-Z]+)\s+
                                VERSION:(?P<VERSION>\d+)\s+
                                SECURITY:(?P<SECURITY>[A-Z]+)\s+
                                ENCODING:(?P<ENCODING>[A-Z]+)\s+
                                CHARSET:(?P<CHARSET>\d+)\s+
                                COMPRESSION:(?P<COMPRESjION>[A-Z]+)\s+
                                OLDFILEUID:(?P<OLDFILEUID>[\w-]+)\s+
                                NEWFILEUID:(?P<NEWFILEUID>[\w-]+)\s+
                                """, re.VERBOSE)

        tests = { 'OFXHEADER': ('100',),
                 'DATA': ('OFXSGML',),
                 'VERSION': ('102', '103'),
                 'SECURITY': ('NONE', 'TYPE1'),
                 'ENCODING': ('UNICODE', 'USASCII')
                }

    class v2(object):
        regex = re.compile(r"""(<\?xml\s+
                                (version=\"(?P<XMLVERSION>[\d.]+)\")?\s*
                                (encoding=\"(?P<ENCODING>[\w-]+)\")?\s*
                                (standalone=\"(?P<STANDALONE>[\w]+)\")?\s*
                                \?>)\s*
                                <\?OFX\s+
                                OFXHEADER=\"(?P<OFXHEADER>\d+)\"\s+
                                VERSION=\"(?P<VERSION>\d+)\"\s+
                                SECURITY=\"(?P<SECURITY>[A-Z]+)\"\s+
                                OLDFILEUID=\"(?P<OLDFILEUID>[\w-]+)\"\s+
                                NEWFILEUID=\"(?P<NEWFILEUID>[\w-]+)\"\s*
                                \?>\s+""", re.VERBOSE)

        tests = { 'OFXHEADER': ('200',),
                 'VERSION': ('200', '203', '211'),
                 'SECURITY': ('NONE', 'TYPE1'),
                }

    @property
    def major_version(self):
        """ Return 1 for OFXv1; 2 for OFXv2 """
        return int(self.version)//100

    def __init__(self, version, newfileuid):
        self.version = version
        self.newfileuid = newfileuid

    def __str__(self):
        if self.major_version == 1:
            # Flat text header
            fields = (  ('OFXHEADER', '100'),
                        ('DATA', 'OFXSGML'),
                        ('VERSION', str(self.version)),
                        ('SECURITY', 'NONE'),
                        ('ENCODING', 'USASCII'),
                        ('CHARSET', '1252'),
                        ('COMPRESSION', 'NONE'),
                        ('OLDFILEUID', 'NONE'),
                        ('NEWFILEUID', str(self.newfileuid)),
            )
            lines = [':'.join(field) for field in fields]
            lines = '\r\n'.join(lines)
            lines += '\r\n'*2
            return lines
        elif self.major_version == 2:
            # XML header
            xml_decl = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            fields = (  ('OFXHEADER', '200'),
                        ('VERSION', str(self.version)),
                        ('SECURITY', 'NONE'),
                        ('OLDFILEUID', 'NONE'),
                        ('NEWFILEUID', str(self.newfileuid)),
            )
            attrs = ['='.join((attr, '"%s"' %val)) for attr,val in fields]
            ofx_decl = '<?OFX %s?>' % ' '.join(attrs)
            return '\r\n'.join((xml_decl, ofx_decl))
        else:
            raise ValueError('Bad OFX version# %s' % self.version)

    @classmethod
    def strip(cls, source):
        # First validate OFX header
        for headerspec in (cls.v1, cls.v2):
            headermatch = headerspec.regex.match(source)
            if headermatch is not None:
                header = headermatch.groupdict()
                try:
                    for (field, valid) in headerspec.tests.items():
                        assert header[field] in valid
                except AssertionError:
                    raise OFXHeaderError('Malformed OFX header %s' % str(header))
                break

        if headermatch is None:
            raise OFXHeaderErro("Can't recognize OFX Header")

        # Strip OFX header and return body
        return source[headermatch.end():]

