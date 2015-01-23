#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import sys
import decimal
import datetime
import time
import calendar
import uuid
#from xml.etree.cElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import SubElement, tostring
from collections import defaultdict, OrderedDict
import contextlib
from io import StringIO
import os
import re
from getpass import getpass

PYTHON_VERSION = sys.version_info.major

if  PYTHON_VERSION == 3:
    from configparser import SafeConfigParser
    from urllib.request import Request, urlopen, HTTPError
    from urllib.parse import urlparse
else:
    from ConfigParser import SafeConfigParser
    from urllib2 import Request, urlopen, HTTPError
    from urlparse import urlparse


# local imports
from lib import ISO639_2, ISO4217, ISO3166_1a3
from converters import OFXElement, OFXbool, OFXstr, OneOf, OFXint, OFXdecimal,\
        OFXdatetime
from utils import fixpath


### CLIENT
class BankAcct:
    """ """
    acctkeys = ('BANKID', 'ACCTID', 'ACCTTYPE')
    acctfrom_tag = 'BANKACCTFROM'
    stmtrq_tag = 'STMTRQ'
    msgsrq_tag = 'BANKMSGSRQV1'

    # 9-digit ABA routing number
    routingre = re.compile('^\d{9}$')

    def __init__(self, bankid, acctid, accttype):
        self._acct = OrderedDict.fromkeys(self.acctkeys)
        accttype = accttype.upper()
        accttype = OneOf(*ACCTTYPES).convert(accttype)
        self._acct['ACCTTYPE'] = OneOf(*ACCTTYPES).convert(accttype)

        bankid = str(bankid)
        if not self.routingre.match(bankid):
            raise ValueError('Invalid bankid %s' % bankid)
        self._acct['BANKID'] = bankid

        assert acctid
        self._acct['ACCTID'] = str(acctid)

    def __repr__(self):
        values = [v for v in self._acct.values()]
        repr_string = '%s(' + ', '.join(["'%s'"]*len(values)) +')'
        values.insert(0, self.__class__.__name__)
        return repr_string % tuple(values)

    def stmtrq(self, inctran=True, dtstart=None, dtend=None, **kwargs):
        """ """
        # **kwargs catches incpos/dtasof
        # Requesting transactions without dtstart/dtend (which is the default)
        # asks for all transactions on record.
        rq = Element(self.stmtrq_tag)
        rq.append(self.acctfrom)
        rq.append(self.inctran(inctran, dtstart, dtend))
        return rq

    @property
    def acctfrom(self):
        """ """
        acctfrom = Element(self.acctfrom_tag)
        for tag, text in self._acct.items():
            SubElement(acctfrom, tag).text = text
        return acctfrom

    def inctran(self, inctran, dtstart, dtend):
        """ """
        tran = Element('INCTRAN')
        if dtstart:
            SubElement(tran, 'DTSTART').text = OFXdatetime.unconvert(dtstart)
        if dtend:
            SubElement(tran, 'DTEND').text = OFXdatetime.unconvert(dtend)
        SubElement(tran, 'INCLUDE').text = OFXbool().unconvert(inctran)
        return tran


class CcAcct(BankAcct):
    """ """
    acctkeys = ('ACCTID')
    acctfrom_tag = 'CCACCTFROM'
    stmtrq_tag = 'CCSTMTRQ'
    msgsrq_tag = 'CREDITCARDMSGSRQV1'

    def __init__(self, acctid):
        self._acct = OrderedDict.fromkeys(self.acctkeys)
        assert acctid
        self._acct['ACCTID'] = str(acctid)

    #def __repr__(self):
        #return '%s(%s)' % (self.__class__.__name__, self.acctid)


class InvAcct(BankAcct):
    """ """
    acctkeys = ('BROKERID', 'ACCTID')
    acctfrom_tag = 'INVACCTFROM'
    stmtrq_tag = 'INVSTMTRQ'
    msgsrq_tag = 'INVSTMTMSGSRQV1'

    def __init__(self, brokerid, acctid):
        self._acct = OrderedDict.fromkeys(self.acctkeys)
        assert brokerid
        self._acct['BROKERID'] = brokerid
        assert acctid
        self._acct['ACCTID'] = str(acctid)

    #def __repr__(self):
        #return '%s(%s)' % (self.__class__.__name__, self.brokerid, self.acctid)

    def stmtrq(self, inctran=True, dtstart=None, dtend=None,
               dtasof=None, incpos=True, incbal=True):
        """ """
        rq = super(InvAcct, self).stmtrq(inctran, dtstart, dtend)
        rq.append(self.incoo())
        rq.append(self.incpos(dtasof, incpos))
        rq.append(self.incbal(incbal))
        return rq

    def incoo(self):
        # Include Open Orders - not implemented
        oo = Element('INCOO')
        oo.text = OFXbool().unconvert(False)
        return oo

    def incpos(self, dtasof, incpos):
        pos = Element('INCPOS')
        if dtasof:
            SubElement(pos, 'DTASOF').text = OFXdatetime.unconvert(dtasof)
        SubElement(pos, 'INCLUDE').text = OFXbool().unconvert(incpos)
        return pos

    def incbal(self, incbal):
        bal = Element('INCBAL')
        bal.text = OFXbool().unconvert(incbal)
        return bal


class OFXClient:
    """ """
    # OFX header/signon defaults
    version = 102
    appid = 'QWIN'
    appver = '1800'

    # Stmt request
    bankid = None
    brokerid = None

    def __init__(self, url, org, fid, version=None, appid=None, appver=None):
        self.url = url
        self.org = org
        self.fid = fid
        # Defaults 
        if version:
            self.version = int(version)
        if appid:
            self.appid = str(appid)
        if appver:
            self.appver = str(appver)

    @property
    def major_version(self):
        """ Return 1 for OFXv1; 2 for OFXv2 """
        return int(self.version)//100

    @property
    def ofxheader_version(self):
        return self.major_version*100

    @property
    def ofxheader(self):
        """ Prepend to OFX markup. """
        if self.major_version == 1:
            # Flat text header
            fields = (  ('OFXHEADER', str(self.ofxheader_version)),
                        ('DATA', 'OFXSGML'),
                        ('VERSION', str(self.version)),
                        ('SECURITY', 'NONE'),
                        ('ENCODING', 'USASCII'),
                        ('CHARSET', '1252'),
                        ('COMPRESSION', 'NONE'),
                        ('OLDFILEUID', 'NONE'),
                        ('NEWFILEUID', str(uuid.uuid4())),
            )
            lines = [':'.join(field) for field in fields]
            lines = '\r\n'.join(lines)
            lines += '\r\n'*2
            return lines
        elif self.major_version == 2:
            # XML header
            xml_decl = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            fields = (  ('OFXHEADER', str(self.ofxheader_version)),
                        ('VERSION', str(self.version)),
                        ('SECURITY', 'NONE'),
                        ('OLDFILEUID', 'NONE'),
                        ('NEWFILEUID', str(uuid.uuid4())),
            )
            attrs = ['='.join((attr, '"%s"' %val)) for attr,val in fields]
            ofx_decl = '<?OFX %s?>' % ' '.join(attrs)
            return '\r\n'.join((xml_decl, ofx_decl))
        else:
            print(self.version)
            # FIXME
            raise ValueError

    def signon(self, user, password):
        msgsrq = Element('SIGNONMSGSRQV1')
        sonrq = SubElement(msgsrq, 'SONRQ')
        SubElement(sonrq, 'DTCLIENT').text = OFXdatetime.unconvert(datetime.datetime.now())
        SubElement(sonrq, 'USERID').text = user
        SubElement(sonrq, 'USERPASS').text = password
        SubElement(sonrq, 'LANGUAGE').text = 'ENG'
        if self.org:
            fi = SubElement(sonrq, 'FI')
            SubElement(fi, 'ORG').text = self.org
            if self.fid:
                SubElement(fi, 'FID').text = self.fid
        SubElement(sonrq, 'APPID').text = self.appid
        SubElement(sonrq, 'APPVER').text = str(self.appver)
        return msgsrq

    def statement_request(self, user, password, accounts, **kwargs):
        """ """
        ofx = Element('OFX')
        ofx.append(self.signon(user, password))

        # Create MSGSRQ SubElements for each acct type, indexed by tag
        msgsrq_tags = [getattr(a, 'msgsrq_tag') for a in (BankAcct, CcAcct, InvAcct)]
        msgsrqs = {tag:SubElement(ofx, tag) for tag in msgsrq_tags}

        for account in accounts:
            stmtrq = account.stmtrq(**kwargs)
            stmttrnrq = self._wraptrn(stmtrq)
            msgsrq = msgsrqs[account.msgsrq_tag]
            msgsrq.append(stmttrnrq)

        # Destroy unused MSGSRQ SubElements, because OFXv1 doesn't like
        # self-closed tags, e.g. <BANKMSGSRQV1 />
        for tag in msgsrqs:
            acct = ofx.find(tag)
            if len(acct) == 0:
                ofx.remove(acct)

        return ofx

    def profile_request(self, user=None, password=None):
        """ """
        user = user or 'elmerfudd'
        password = password or 'TOPSECRET'
        ofx = Element('OFX')
        ofx.append(self.signon(user, password))
        msgsrq = SubElement(ofx, 'PROFMSGSRQV1')
        profrq = Element('PROFRQ')
        SubElement(profrq, 'CLIENTROUTING').text = 'NONE'
        SubElement(profrq, 'DTPROFUP').text = OFXdatetime.unconvert(datetime.date(1990,1,1))
        msgsrq.append(self._wraptrn(profrq))
        return ofx

    def download(self, request):
        """ """
        mimetype = 'application/x-ofx'
        HTTPheaders = {'Content-type': mimetype, 'Accept': '*/*, %s' % mimetype}
        # py3k - ElementTree.tostring() returns bytes not str
        request = self.ofxheader + tostring(request).decode()
        # py3k: urllib.request wants bytes not str
        request = Request(self.url, request.encode(), HTTPheaders)
        try:
            with contextlib.closing(urlopen(request)) as response:
                # py3k: urlopen returns bytes not str
                response_ = response.read().decode()
                # urllib2.urlopen returns an addinfourl instance, which supports
                # a limited subset of file methods.  Copy response to a StringIO
                # so that we can use tell() and seek().
                source = StringIO()
                source.write(response_)
                # After writing, rewind to the beginning.
                source.seek(0)
                self.response = source
                return source
        except HTTPError as err:
            # FIXME
            print(err.info())
            raise

    def _wraptrn(self, rq):
        """ """
        tag = rq.tag
        assert 'TRNRQ' not in tag
        assert tag[-2:] == 'RQ'
        trnrq = Element(tag.replace('RQ', 'TRNRQ'))
        SubElement(trnrq, 'TRNUID').text = str(uuid.uuid4())
        trnrq.append(rq)
        return trnrq

### PARSER
class ParseError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class OFXHeaderSpec(object):
    """ 
    """
    class v1(object):
        regex = re.compile(r"""\s*
                                OFXHEADER:(?P<OFXHEADER>\d+)\s+
                                DATA:(?P<DATA>[A-Z]+)\s+
                                VERSION:(?P<VERSION>\d+)\s+
                                SECURITY:(?P<SECURITY>[A-Z]+)\s+
                                ENCODING:(?P<ENCODING>[A-Z]+)\s+
                                CHARSET:(?P<CHARSET>\d+)\s+
                                COMPRESSION:(?P<COMPRESSION>[A-Z]+)\s+
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
                    raise ParseError('Malformed OFX header %s' % str(header))
                break

        if headermatch is None:
            raise ParseError("Can't recognize OFX Header")

        # Strip OFX header and return body
        return source[headermatch.end():]


class ElementTree(ET.ElementTree):
    """ 
    Subclass of ElementTree.Element Tree with custom parse() method that 
    validates/strips the OFX header, then feeds the body tags to custom
    TreeBuilder subclass
    """
    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source)
        source = source.read()

        # Validate and strip the OFX header
        source = OFXHeaderSpec.strip(source)

        # Then parse tag soup into tree of Elements
        parser = TreeBuilder(element_factory=Element)
        parser.feed(source)
        self._root = parser.close()

    def convert(self):
        if not hasattr(self, '_root'):
            raise ValueError('Must first call parse() to have data to convert')
        # OFXResponse performs validation & type conversion
        return OFXResponse(self)


OFXParser = ElementTree


class TreeBuilder(ET.TreeBuilder):
    """ 
    Subclass of ElementTree.TreeBuilder with a custom feed() method implementing
    a regex-based parser for SGML
    """
    # The body of an OFX document consists of a series of tags.
    # Each start tag may be followed by text (if a data-bearing element)
    # and optionally an end tag (not mandatory for OFXv1 syntax).
    regex = re.compile(r"""<(?P<TAG>[A-Z1-9./]+?)>
                            (?P<TEXT>[^<]+)?
                            (</(?P=TAG)>)?
                            """, re.VERBOSE)

    def feed(self, data):
        """
        Iterate through all tags matched by regex.
        For data-bearing leaf "elements", use TreeBuilder's methods to
            push a new Element, process the text data, and end the element.
        For non-data-bearing "aggregate" branches, parse the tag to distinguish
            start/end tag, and push or pop the Element accordingly.
        """
        for match in self.regex.finditer(data):
            tag, text, closeTag = match.groups()
            text = (text or '').strip() # None has no strip() method
            if len(text):
                # OFX "element" (i.e. data-bearing leaf)
                if tag.startswith('/'):
                    msg = "<%s> is a closing tag, but has trailing text: '%s'"\
                            % (tag, text)
                    raise ParseError(msg)
                self.start(tag, {})
                self.data(text)
                # End tags are optional for OFXv1 data elements
                # End them all, whether or not they're explicitly ended
                try:
                    self.end(tag)
                except ParseError as err:
                    err.message += ' </%s>' % tag # FIXME
                    raise ParseError(err.message)
            else:
                # OFX "aggregate" (tagged branch w/ no data)
                if tag.startswith('/'):
                    # aggregate end tag
                    try:
                        self.end(tag[1:])
                    except ParseError as err:
                        err.message += ' </%s>' % tag # FIXME
                        raise ParseError(err.message)
                else:
                    # aggregate start tag
                    self.start(tag, {})
                    # empty aggregates are legal, so handle them
                    if closeTag:
                        # regex captures the entire closing tag
                       assert closeTag.replace(tag, '') == '</>'
                       try:
                           self.end(tag)
                       except ParseError as err:
                           err.message += ' </%s>' % tag # FIXME
                           raise ParseError(err.message)

    def end(self, tag):
        try:
            super(TreeBuilder, self).end(tag)
        except AssertionError as err:
            # HACK: ET.TreeBuilder.end() raises an AssertionError for internal
            # errors generated by ET.TreeBuilder._flush(), but also for ending
            # tag mismatches, which are problems with the data rather than the
            # parser.  We want to pass on the former but handle the latter;
            # however, the only difference is the error message.
            if 'end tag mismatch' in err.message:
                raise ParseError(err.message)
            else:
                raise


class Element(ET.Element):
    """ 
    Subclass of ElementTree.Element extended to handle validation and type
    conversion of OFX Aggregates.
    """
    def convert(self):
        """ 
        Convert a parsed OFX aggregate into a flat dictionary of its elements
        """
        attributes = self._flatten()

        # Converters are named after the tags they service; look it up.
        converter = globals()[self.tag]
        assert issubclass(converter, Aggregate)

        # See OFX spec section 5.2 for currency handling conventions.
        # Flattening the currency definition leaves only the CURRATE/CURSYM
        # elements, leaving no indication of whether these were sourced from
        # a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        # important to interpreting transactions in foreign correncies, we
        # preserve this information by adding a nonstandard curtype element.
        if issubclass(converter, ORIGCURRENCY):
            currency = self.find('*/CURRENCY')
            origcurrency = self.find('*/ORIGCURRENCY')
            if (currency is not None) and (origcurrency is not None):
                raise ParseError("<%s> may not contain both <CURRENCY> and \
                                 <ORIGCURRENCY>" % self.tag)
            curtype = currency
            if curtype is None:
                 curtype = origcurrency
            if curtype is not None:
                curtype = curtype.tag
            attributes['curtype'] = curtype

        # Feed the flattened dictionary of attributes to the converter
        return converter(**attributes)


    def _flatten(self):
        """
        Recurse through aggregate and flatten; return an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
        """
        aggregates = {}
        leaves = {}
        for child in self:
            tag = child.tag
            data = child.text or ''
            data = data.strip()
            if data:
                # it's a data-bearing leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # it's an aggregate.
                assert tag not in aggregates
                aggregates.update(child._flatten())
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggregates.keys():
            assert key not in leaves
        leaves.update(aggregates)
        return leaves


### PYTHON OFX OBJECT MODEL
class OFXResponse(object):
    """ 
    Top-level object representing an OFX response converted into Python
    data types, with attributes for convenient access to statements,
    SECLIST (description of referenced securities), and SONRS (server response
    to signon request).

    After conversion, each of these convenience attributes holds
    """
    sonrs = None
    statements = []
    seclist = []

    def __init__(self, tree):
        """ Initialize with ElementTree instance containing parsed OFX """
        self._root = tree._root
        self.process()

    def process(self):
        """ Top-level entry point into validation & conversion of parsed OFX """
        self._processSONRS()
        self._processTRNRS()
        self._processSECLIST()

    def _processSONRS(self):
        """ Validate/convert server response to signon request """
        sonrs = self._root.find('SIGNONMSGSRSV1/SONRS')
        self.sonrs = sonrs.convert()

    def _processTRNRS(self):
        """
        Validate/convert transaction response, which is the main section
        containing account statements
        """
        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        for stmtClass in (STMT, CCSTMT, INVSTMT):
            classname = stmtClass.__name__
            for trnrs in self._root.findall('*/%sTRNRS' % classname):
                stmtrs = trnrs.find('%sRS' % classname)
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                if stmtrs is not None:
                    stmt = stmtClass(stmtrs)
                    # Staple the TRNRS wrapper data onto the STMT
                    stmt.trnuid = OFXstr(36).convert(trnrs.find('TRNUID').text)
                    stmt.status = trnrs.find('STATUS').convert()
                    cltcookie = trnrs.find('CLTCOOKIE')
                    if cltcookie is not None:
                        stmt.cltcookie = OFXstr(36).convert(cltcookie.text)
                    self.statements.append(stmt)

    def _processSECLIST(self):
        """ 
        Validate/convert the list of description of securities referenced by
        INVSTMT (investment account statement
        """
        seclist = self._root.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is None:
            return
        for sec in seclist:
            if sec.tag == 'MFINFO':
                # Strip MFASSETCLASS/FIMFASSETCLASS 
                # - lists that will blow up _flatten()
                mfassetclass = sec.find('./MFASSETCLASS')
                if mfassetclass is not None:
                    # Convert PORTIONs; add to list on MFINFO
                    sec.mfassetclass = [p.convert() for p in mfassetclass]
                    sec.remove(mfassetclass)
                fimfassetclass = sec.find('./FIMFASSETCLASS')
                if fimfassetclass is not None:
                    # Convert FIPORTIONs; add to list on MFINFO
                    sec.fimfassetclass = [p.convert() for p in fimfassetclass]
                    sec.remove(fimfassetclass)

            self.seclist.append(sec.convert())


    def __repr__(self):
        return '<%s at at 0x%x>' % (self.__class__.__name__, id(self))


class BaseSTMT(object):
    """ Base class for Python representation of OFX *STMT aggregate """
    # From TRNRS wrapper
    trnuid = None
    status = None
    cltcookie = None

    curdef = None
    acctfrom = None

    tranlist = None
    ballist = None

    def __init__(self, stmtrs):
        """ Initialize with *STMTRS Element """
        self.curdef = stmtrs.find('CURDEF').text
        self.acctfrom = stmtrs.find(self._acctTag).convert()
        self.process(stmtrs)

    def process(self, stmtrs):
        # Define in subclass
        raise NotImplementedError

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))


class STMT(BaseSTMT):
    """ Python representation of OFX STMT (bank statement) aggregate """
    ledgerbal = None
    availbal = None

    _acctTag = 'BANKACCTFROM'

    @property
    def bankacctfrom(self):
        return self.acctfrom

    @bankacctfrom.setter
    def bankacctfrom(self, value):
        self.acctfrom = value

    @property
    def banktranlist(self):
        return self.tranlist

    @banktranlist.setter
    def banktranlist(self, value):
        self.tranlist = value

    def process(self, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            self.tranlist = BANKTRANLIST(tranlist)

        # LEDGERBAL - mandatory
        self.ledgerbal = stmtrs.find('LEDGERBAL').convert()

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            self.availbal = availbal.convert()

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.ballist = [bal.convert() for bal in ballist]

        # Unsupported subaggregates
        for tag in ('MKTGINFO', ):
            child = stmtrs.find(tag)
            if child:
                stmtrs.remove


class CCSTMT(STMT):
    """ 
    Python representation of OFX CCSTMT (credit card statement) 
    aggregate 
    """
    _acctTag = 'CCACCTFROM'

    @property
    def ccacctfrom(self):
        return self.acctfrom

    @ccacctfrom.setter
    def ccacctfrom(self, value):
        self.acctfrom = value


class INVSTMT(BaseSTMT):
    """ 
    Python representation of OFX INVSTMT (investment account statement) 
    aggregate 
    """
    dtasof = None

    invposlist = None
    invbal = None

    _acctTag = 'INVACCTFROM'

    @property
    def invacctfrom(self):
        return self.acctfrom

    @invacctfrom.setter
    def invacctfrom(self, value):
        self.acctfrom = value

    @property
    def invtranlist(self):
        return self.tranlist

    @invtranlist.setter
    def invtranlist(self, value):
        self.tranlist = value

    def process(self, invstmtrs):
        dtasof = invstmtrs.find('DTASOF').text
        self.dtasof = OFXdatetime.convert(dtasof)

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            self.tranlist = INVTRANLIST(tranlist)

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            self.invposlist = [pos.convert() for pos in poslist]

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal is not None:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist is not None:
                invbal.remove(ballist)
                self.ballist = [bal.convert() for bal in ballist]
            # Now we can flatten the rest of INVBAL
            self.invbal = invbal.convert()

        # Unsupported subaggregates
        for tag in ('INVOOLIST', 'INV401K', 'INV401KBAL', 'MKTGINFO'):
            child = invstmtrs.find(tag)
            if child is not None:
                invstmtrs.remove


class TRANLIST(list):
    """ 
    Base class for Python representation of OFX *TRANLIST (transaction list) 
    aggregate 
    """
    def __init__(self, tranlist):
        # Initialize with *TRANLIST Element
        dtstart, dtend = tranlist[0:2]
        tranlist = tranlist[2:]
        self.dtstart = OFXdatetime.convert(dtstart.text)
        self.dtend = OFXdatetime.convert(dtend.text)
        self.extend([tran.convert() for tran in tranlist])

    def __repr__(self):
        return "<%s dtstart='%s' dtend='%s' #transactions=%s>" % (self.__class__.__name__, self.dtstart, self.dtend, len(self))


class BANKTRANLIST(TRANLIST):
    """
    Python representation of OFX BANKTRANLIST (bank transaction list) 
    aggregate
    """
    pass


class INVTRANLIST(TRANLIST):
    """
    Python representation of OFX INVTRANLIST (investment transaction list)
    aggregate 
    """
    pass


# Enums used in aggregate validation
INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING',
                    'ROLLOVER', 'OTHERVEST', 'OTHERNONVEST')
ACCTTYPES = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')


class Aggregate(object):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML parent
    node that contains no data.  Data-bearing OFXElements are represented as
    attributes of the containing Aggregate.

    The Aggregate class is implemented as a data descriptor that, before
    setting an attribute, checks whether that attribute is defined as
    an OFXElement in the class definition.  If it is, the OFXElement's type
    conversion method is called, and the resulting value stored in the
    Aggregate instance's __dict__.
    """
    def __init__(self, **kwargs):
        for name, element in self.elements.items():
            value = kwargs.pop(name, None)
            if element.required and value is None:
                raise ValueError("'%s' attribute is required for %s"
                                % (name, self.__class__.__name__))
            setattr(self, name, value)
        if kwargs:
            raise ValueError("Undefined element(s) for '%s': %s"
                            % (self.__class__.__name__, kwargs.keys()))

    @property
    def elements(self):
        d = {}
        for m in self.__class__.__mro__:
            d.update({k: v for k,v in m.__dict__.items() \
                                    if isinstance(v, OFXElement)})
        return d

    def __getattribute__(self, name):
        if name.startswith('__'):
            # Short-circuit private attributes to avoid infinite recursion
            attribute = object.__getattribute__(self, name)
        elif isinstance(getattr(self.__class__, name), OFXElement):
            # Don't inherit OFXElement attributes from class
            attribute = self.__dict__[name]
        else:
            attribute = object.__getattribute__(self, name)
        return attribute

    def __setattr__(self, name, value):
        """ If attribute references an OFXElement, convert before setting """
        classattr = getattr(self.__class__, name)
        if isinstance(classattr, OFXElement):
            value = classattr.convert(value)
        object.__setattr__(self, name, value)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, ' '.join(['%s=%r' % (attr, getattr(self, attr)) for attr in self.elements.viewkeys() if getattr(self, attr) is not None]))


class FI(Aggregate):
    """
    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    """
    org = OFXstr(32)
    fid = OFXstr(32)


class STATUS(Aggregate):
    code = OFXint(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = OFXstr(255)


class SONRS(FI, STATUS):
    dtserver = OFXdatetime(required=True)
    userkey = OFXstr(64)
    tskeyexpire = OFXdatetime()
    language = OneOf(*ISO639_2)
    dtprofup = OFXdatetime()
    dtacctup = OFXdatetime()
    sesscookie = OFXstr(1000)
    accesskey = OFXstr(1000)


class CURRENCY(Aggregate):
    cursym = OneOf(*ISO4217)
    currate = OFXdecimal(8)


class ORIGCURRENCY(CURRENCY):
    curtype = OneOf('CURRENCY', 'ORIGCURRENCY')


class ACCTFROM(Aggregate):
    acctid = OFXstr(22, required=True)


class BANKACCTFROM(ACCTFROM):
    bankid = OFXstr(9, required=True)
    branchid = OFXstr(22)
    accttype = OneOf(*ACCTTYPES,
                    required=True)
    acctkey = OFXstr(22)


class BANKACCTTO(BANKACCTFROM):
    pass


class CCACCTFROM(ACCTFROM):
    acctkey = OFXstr(22)


class CCACCTTO(CCACCTFROM):
    pass


class INVACCTFROM(ACCTFROM):
    brokerid = OFXstr(22, required=True)


# Balances
class LEDGERBAL(Aggregate):
    balamt = OFXdecimal(required=True)
    dtasof = OFXdatetime(required=True)


class AVAILBAL(Aggregate):
    balamt = OFXdecimal(required=True)
    dtasof = OFXdatetime(required=True)


class INVBAL(Aggregate):
    availcash = OFXdecimal(required=True)
    marginbalance = OFXdecimal(required=True)
    shortbalance = OFXdecimal(required=True)
    buypower = OFXdecimal()


class BAL(CURRENCY):
    name = OFXstr(32, required=True)
    desc = OFXstr(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = OFXdecimal(required=True)
    dtasof = OFXdatetime()


# Securities
class SECID(Aggregate):
    uniqueid = OFXstr(32, required=True)
    uniqueidtype = OFXstr(10, required=True)


class SECINFO(CURRENCY, SECID):
    secname = OFXstr(120, required=True)
    ticker = OFXstr(32)
    fiid = OFXstr(32)
    rating = OFXstr(10)
    unitprice = OFXdecimal()
    dtasof = OFXdatetime()
    memo = OFXstr(255)


class DEBTINFO(SECINFO):
    parvalue = OFXdecimal(required=True)
    debttype = OneOf('COUPON', 'ZERO', required=True)
    debtclass = OneOf('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER')
    couponrt = OFXdecimal(4)
    dtcoupon = OFXdatetime()
    couponfreq = OneOf('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                            'OTHER')
    callprice = OFXdecimal(4)
    yieldtocall = OFXdecimal(4)
    dtcall = OFXdatetime()
    calltype = OneOf('CALL', 'PUT', 'PREFUND', 'MATURITY')
    ytmat = OFXdecimal(4)
    dtmat = OFXdatetime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


class MFINFO(SECINFO):
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = OFXdecimal(4)
    dtyieldasof = OFXdatetime()


class PORTION(Aggregate):
    assetclass = OneOf(*ASSETCLASSES)
    percent = OFXdecimal()


class FIPORTION(Aggregate):
    fiassetclass = OFXstr(32)
    percent = OFXdecimal()


class OPTINFO(SECINFO):
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = OFXdecimal(required=True)
    dtexpire = OFXdatetime(required=True)
    shperctrct = OFXint(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


class OTHERINFO(SECINFO):
    typedesc = OFXstr(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


class STOCKINFO(SECINFO):
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = OFXdecimal(4)
    dtyieldasof = OFXdatetime()
    typedesc = OFXstr(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


# Transactions
class PAYEE(Aggregate):
    name = OFXstr(32, required=True)
    addr1 = OFXstr(32, required=True)
    addr2 = OFXstr(32)
    addr3 = OFXstr(32)
    city = OFXstr(32, required=True)
    state = OFXstr(5, required=True)
    postalcode = OFXstr(11, required=True)
    country = OneOf(*ISO3166_1a3)
    phone = OFXstr(32, required=True)


class TRAN(Aggregate):
    fitid = OFXstr(255, required=True)
    srvrtid = OFXstr(10)


class STMTTRN(TRAN, ORIGCURRENCY):
    trntype = OneOf('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
                    'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
                    'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
                    'OTHER', required=True)
    dtposted = OFXdatetime(required=True)
    dtuser = OFXdatetime()
    dtavail = OFXdatetime()
    trnamt = OFXdecimal(required=True)
    correctfitid = OFXdecimal()
    correctaction = OneOf('REPLACE', 'DELETE')
    checknum = OFXstr(12)
    refnum = OFXstr(32)
    sic = OFXint()
    payeeid = OFXstr(12)
    name = OFXstr(32)
    memo = OFXstr(255)
    inv401ksource = OneOf(*INV401KSOURCES)

    payee = None
    bankacctto = None
    ccacctto = None


class INVBANKTRAN(STMTTRN):
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class INVTRAN(TRAN):
    dttrade = OFXdatetime(required=True)
    dtsettle = OFXdatetime()
    reversalfitid = OFXstr(255)
    memo = OFXstr(255)


class INVBUY(INVTRAN, SECID, ORIGCURRENCY):
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    markup = OFXdecimal()
    commission = OFXdecimal()
    taxes = OFXdecimal()
    fees = OFXdecimal()
    load = OFXdecimal()
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS)
    subacctfund = OneOf(*INVSUBACCTS)
    loanid = OFXstr(32)
    loanprincipal = OFXdecimal()
    loaninterest = OFXdecimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = OFXdatetime()
    prioryearcontrib = OFXbool()


class INVSELL(INVTRAN, SECID, ORIGCURRENCY):
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    markdown = OFXdecimal()
    commission = OFXdecimal()
    taxes = OFXdecimal()
    fees = OFXdecimal()
    load = OFXdecimal()
    withholding = OFXdecimal()
    taxexempt = OFXbool()
    total = OFXdecimal(required=True)
    gain = OFXdecimal()
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = OFXstr(32)
    statewithholding = OFXdecimal()
    penalty = OFXdecimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class BUYDEBT(INVBUY):
    accrdint = OFXdecimal()


class BUYMF(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = OFXstr(255)


class BUYOPT(INVBUY):
    optbuytype = OneOf('BUYTOOPEN', 'BUYTOCLOSE', required=True)
    shperctrct = OFXint(required=True)


class BUYOTHER(INVBUY):
    pass


class BUYSTOCK(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(INVTRAN, SECID):
    optaction = OneOf('EXERCISE', 'ASSIGN', 'EXPIRE')
    units = OFXdecimal(required=True)
    shperctrct = OFXint(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = OFXstr(255)
    gain = OFXdecimal()


class INCOME(INVTRAN, SECID, ORIGCURRENCY):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = OFXbool()
    withholding = OFXdecimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(INVTRAN, SECID, ORIGCURRENCY):
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(INVTRAN):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = OFXdecimal(required=True)


class JRNLSEC(INVTRAN, SECID):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = OFXdecimal(required=True)


class MARGININTEREST(INVTRAN, ORIGCURRENCY):
    total = OFXdecimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class REINVEST(INVTRAN, SECID, ORIGCURRENCY):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS)
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    commission = OFXdecimal()
    taxes = OFXdecimal()
    fees = OFXdecimal()
    load = OFXdecimal()
    taxexempt = OFXbool()
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(INVTRAN, SECID, ORIGCURRENCY):
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(INVSELL):
    sellreason = OneOf('CALL', 'SELL', 'MATURITY', required=True)
    accrdint = OFXdecimal()


class SELLMF(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = OFXdecimal()
    relfitid = OFXstr(255)


class SELLOPT(INVSELL):
    optselltype = OneOf('SELLTOCLOSE', 'SELLTOOPEN', required=True)
    shperctrct = OFXint(required=True)
    relfitid = OFXstr(255)
    reltype = OneOf('SPREAD', 'STRADDLE', 'NONE', 'OTHER')
    secured = OneOf('NAKED', 'COVERED')


class SELLOTHER(INVSELL):
    pass


class SELLSTOCK(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)


class SPLIT(INVTRAN, SECID):
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    oldunits = OFXdecimal(required=True)
    newunits = OFXdecimal(required=True)
    numerator = OFXdecimal(required=True)
    denominator = OFXdecimal(required=True)
    fraccash = OFXdecimal()
    subacctfund = OneOf(*INVSUBACCTS)
    inv401ksource = OneOf(*INV401KSOURCES)


class TRANSFER(INVTRAN, SECID):
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = OFXdecimal(required=True)
    tferaction = OneOf('IN', 'OUT', required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    avgcostbasis = OFXdecimal()
    unitprice = OFXdecimal()
    dtpurchase = OFXdatetime()
    inv401ksource = OneOf(*INV401KSOURCES)


# Positions
class INVPOS(SECID, CURRENCY):
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    mktval = OFXdecimal(required=True)
    dtpriceasof = OFXdatetime(required=True)
    memo = OFXstr(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = OFXdecimal()
    unitsuser = OFXdecimal()
    reinvdiv = OFXbool()
    reinvcg = OFXbool()


class POSOPT(INVPOS):
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    pass


class POSSTOCK(INVPOS):
    unitsstreet = OFXdecimal()
    unitsuser = OFXdecimal()
    reinvdiv = OFXbool()


### CLI COMMANDS
def do_config(args):
    # FIXME
    server = args.server
    if server not in config.fi_index:
        raise ValueError("Unknown FI '%s' not in %s"
                        % (server, str(config.fi_index)))
    print(str(dict(config.items(server))))

def do_profile(args):
    client = OFXClient(args.url, args.org, args.fid, 
                       version=args.version, appid=args.appid, appver=args.appver)

    # Always use dummy password - initial profile request
    password = 'T0PS3CR3T'
    request = client.profile_request(args.user, password)

    # Handle request
    if args.dry_run:
        print(client.ofxheader + tostring(request).decode())
    else:
        response = client.download(request)
        print(response.read())

def do_stmt(args):
    client = OFXClient(args.url, args.org, args.fid, 
                       version=args.version, appid=args.appid, appver=args.appver)

    # Define accounts
    accts = []
    for accttype in ('checking', 'savings', 'moneymrkt', 'creditline'):
        #print(accts)
        for acctid in getattr(args, accttype):
            a = BankAcct(args.bankid, acctid, accttype)
            accts.append(a)

    for acctid in args.creditcard:
        accts.append(CcAcct(acctid))

    for acctid in args.investment:
        accts.append(InvAcct(args.brokerid, acctid))

    # Use dummy password for dummy request
    if args.dry_run:
        password = 'T0PS3CR3T'
    else:
        password = getpass()

    # Statement parameters
    d = vars(args)
    # convert dtstart/dtend/dtasof from str to datetime
    kwargs = {k:OFXdatetime.convert(v) for k,v in d.items() if k.startswith('dt')}
    # inctrans/incpos/incbal 
    kwargs.update({k:v for k,v in d.items() if k.startswith('inc')})

    request = client.statement_request(args.user, password, accts, **kwargs)

    # Handle request
    if args.dry_run:
        print(client.ofxheader + tostring(request).decode())
    else:
        response = client.download(request)
        print(response.read())


class OFXConfigParser(SafeConfigParser):
    """ """
    main_config = os.path.join(os.path.dirname(__file__), 'main.cfg')

    def __init__(self):
        SafeConfigParser.__init__(self)

    def read(self, filenames=None):
        # Load main config
        self.readfp(open(fixpath(self.main_config)))
        # Then load user configs (defaults to main.cfg [global] config: value)
        filenames = filenames or fixpath(self.get('global', 'config'))
        return SafeConfigParser.read(self, filenames)

    @property
    def fi_index(self):
        sections = self.sections()
        sections.remove('global')
        return sections


if __name__ == '__main__':
    # Read config first, so fi_index can be used in help
    config = OFXConfigParser()
    config.read()

    from argparse import ArgumentParser

    #usage = "usage: %(prog)s [options] institution"
    #argparser = ArgumentParser(usage=usage)
    argparser = ArgumentParser(description='Download OFX financial data',
                                epilog='FIs configured: %s' % config.fi_index)
    argparser.add_argument('server', help='OFX server - URL or FI name from config')
    #argparser.add_argument('action', nargs='?', choices=('stmt', 'profile', 'config'),
                          #default='stmt', help='OFX statement|OFX profile|Configured settings')
    argparser.add_argument('-n', '--dry-run', action='store_true', 
                           default=False, help='display OFX request and exit')

    signon_group = argparser.add_argument_group(title='signon options')
    signon_group.add_argument('-u', '--user', help='FI login username')
    signon_group.add_argument('--org', help='FI.ORG')
    signon_group.add_argument('--fid', help='FI.FID')
    signon_group.add_argument('--version', help='OFX version')
    signon_group.add_argument('--appid', help='OFX client app identifier')
    signon_group.add_argument('--appver', help='OFX client app version')

    subparsers = argparser.add_subparsers(title='subcommands',
                                          description='FOOBAR',
                                          # Would be nice to add this:
                                          # http://bugs.python.org/issue9253
                                          #default='stmt',
                                          help='help help help')
    subparser_config = subparsers.add_parser('config', help='Display FI configurations and exit')
    subparser_config.set_defaults(func=do_config)

    subparser_profile = subparsers.add_parser('profile', help='helpity help')
    subparser_profile.set_defaults(func=do_profile)

    subparser_stmt = subparsers.add_parser('stmt', help='helpity help')
    subparser_stmt.set_defaults(func=do_stmt)

    acct_group = subparser_stmt.add_argument_group(title='account options')
    acct_group.add_argument('--bankid', help='ABA routing#')
    acct_group.add_argument('--brokerid', help='Broker ID string')
    acct_group.add_argument('-C', '--checking', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-S', '--savings', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-M', '--moneymrkt', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-L', '--creditline', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-c', '--creditcard', '--cc', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-i', '--investment', metavar='acct#', action='append', default=[])

    stmt_group = subparser_stmt.add_argument_group(title='statement options')
    stmt_group.add_argument('-s', '--start', dest='dtstart', help='Start date/time for transactions')
    stmt_group.add_argument('-e', '--end', dest='dtend', help='End date/time for transactions')
    stmt_group.add_argument('--no-transactions', dest='inctran',
                            action='store_false', default=True)
    stmt_group.add_argument('-d', '--date', dest='dtasof', help='As-of date for investment positions')
    stmt_group.add_argument('--no-positions', dest='incpos',
                            action='store_false', default=True)
    stmt_group.add_argument('--no-balances', dest='incbal',
                            action='store_false', default=True)

    args = argparser.parse_args()

    # If positional arg is FI name (not URL), then merge config
    server = args.server
    if urlparse(server).scheme:
        args.url = server
    else:
        if server not in config.fi_index:
            raise ValueError("Unknown FI '%s' not in %s"
                            % (server, str(config.fi_index)))
        # List of nonempty argparse args set from command line
        overrides = [k for k,v in vars(args).items() if v]
        for cfg, value in config.items(server, raw=True):
            # argparse settings override configparser settings
            if cfg in overrides:
                continue
            if cfg in ('checking', 'savings', 'moneymrkt', 'creditline',
                       'creditcard', 'investment'):
                # Allow sequences of acct nos
                values = [v.strip() for v in value.split(',')]
                arg = getattr(args, cfg)
                assert isinstance(arg, list)
                arg.extend(values)
            else:
                setattr(args, cfg, value)

    # Execute subparser callback, passing merged argparse/configparser args
    args.func(args)

