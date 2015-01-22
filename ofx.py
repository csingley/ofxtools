#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import decimal
import datetime
import time
import calendar
import uuid
from xml.etree.cElementTree import Element, SubElement, tostring
from collections import defaultdict, OrderedDict
import contextlib
from io import StringIO
import os
import re
import xml.etree.ElementTree as ET
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

class OFXHeaderSpec(object):
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


class OFXParser(ET.ElementTree):
    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source)
        source = source.read()

        ### First parse OFX header
        for headerspec in (OFXHeaderSpec.v1, OFXHeaderSpec.v2):
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
        source = source[headermatch.end():]

        ### Then parse tag soup into tree of Elements
        parser = OFXTreeBuilder(element_factory=Element)
        parser.feed(source)
        self._root = parser.close()

        ### OFXResponse performs validation & type conversion
        self.response = OFXResponse(self._root)
        self.response.process()
        return self.response


class OFXTreeBuilder(ET.TreeBuilder):
    """ """
    regex = re.compile(r"""<(?P<TAG>[A-Z1-9./]+?)>
                            (?P<TEXT>[^<]+)?
                            (</(?P=TAG)>)?
                            """, re.VERBOSE)

    def __init__(self, element_factory=None):
        self.tagCount = defaultdict(int)
        self.closeTagCount = defaultdict(int)
        super(OFXTreeBuilder, self).__init__(element_factory)

    def feed(self, data):
        for match in self.regex.finditer(data):
            tag, text, closeTag = match.groups()
            self.tagCount[tag] += 1
            self.closeTagCount[closeTag] += 1
            text = (text or '').strip() # None has no strip() method
            if len(text):
                # OFX "element" (i.e. data-bearing leaf)
                if tag.startswith('/'):
                    msg = "<%s> is a closing tag, but has trailing text: '%s'"\
                            % (tag, text)
                    raise ParseError(msg)
                self.start(tag, {})
                self.data(text)
                # Closing tags are optional for OFXv1 data elements
                # Close them all, whether or not they're explicitly closed
                try:
                    self.end(tag)
                except ParseError as err:
                    err.message += ' </%s> #%s' % (tag, self.tagCount[tag]) # FIXME
                    raise ParseError(err.message)
            else:
                # OFX "aggregate" (tagged branch w/ no data)
                if tag.startswith('/'):
                    # aggregate closing tag
                    assert not text
                    try:
                        self.end(tag[1:])
                    except ParseError as err:
                        err.message += ' </%s> #%s' % (tag, self.tagCount[tag]) # FIXME
                        raise ParseError(err.message)
                else:
                    # aggregate opening tag
                    self.start(tag, {})
                    if closeTag:
                        # regex captures the entire closing tag
                       assert closeTag.replace(tag, '') == '</>'
                       try:
                           self.end(tag)
                       except ParseError as err:
                           err.message += ' </%s> #%s' % (tag, self.tagCount[tag]) # FIXME
                           raise ParseError(err.message)

    def end(self, tag):
        try:
            super(OFXTreeBuilder, self).end(tag)
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
    """ """
    #currencyTags = ()
    #origcurrencyAggregates = (STMTTRN, INVBUY,
                            #INVSELL, INCOME,
                            #INVEXPENSE, MARGININTEREST,
                            #REINVEST, RETOFCAP)
    def convert(self):
        """ """
        #converterClass = getattr(converters, self.tag)
        converterClass = globals()[self.tag]
        assert issubclass(converterClass, Aggregate)
        attributes = self._flatten()

        if issubclass(converterClass, ORIGCURRENCY):
            currency = self.find('*/CURRENCY')
            origcurrency = self.find('*/ORIGCURRENCY')
            if (currency is not None) and (origcurrency is not None):
                raise ParseError() # FIXME
            curtype = currency
            if curtype is None:
                 curtype = origcurrency
            if curtype is not None:
                curtype = curtype.tag
            attributes['curtype'] = curtype

        aggregate = converterClass(**attributes)

        return aggregate


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
            data = child.text
            if data is not None:
                data = data.strip()
            if data:
                # element is a leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # element is an aggregate.
                assert tag not in aggregates
                aggregates.update(child._flatten())
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggregates.keys():
            assert key not in leaves
        leaves.update(aggregates)
        return leaves


class OFXResponse(object):
    """ """
    sonrs = None
    statements = []
    seclist = []

    def __init__(self, _root):
        """ Initialize with root Element."""
        self._root = _root

    def process(self):
        self._processSONRS()
        self._processTRNRS()
        self._processSECLIST()

    def _processSONRS(self):
        sonrs = self._root.find('SIGNONMSGSRSV1/SONRS')
        self.sonrs = sonrs.convert()

    def _processTRNRS(self):
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
        seclist = self._root.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is None:
            return
        for sec in seclist:
            # Strip MFASSETCLASS/FIMFASSETCLASS - lists that will blow up _flatten()
            mfassetclass = sec.find('MFASSETCLASS')
            if mfassetclass:
                sec.remove(mfassetclass)
                for portion in mfassetclass:
                    sec.mfassetclass.append(mfassetclass.convert())
            fimfassetclass = sec.find('FIMFASSETCLASS')
            if fimfassetclass:
                sec.remove(fimfassetclass)
                for portion in mfassetclass:
                    sec.fimfassetclass.append(fimfassetclass.convert())
            self.seclist.append(sec.convert())

    def __repr__(self):
        return '<%s at at 0x%x>' % (self.__class__.__name__, id(self))


class BaseSTMT(object):
    """ """
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
    _acctTag = 'CCACCTFROM'

    @property
    def ccacctfrom(self):
        return self.acctfrom

    @ccacctfrom.setter
    def ccacctfrom(self, value):
        self.acctfrom = value


class INVSTMT(BaseSTMT):
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
    """ """
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
    pass


class INVTRANLIST(TRANLIST):
    pass


class ParseError(SyntaxError):
    """ """
    pass


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


### CONVERTERS
INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING',
                    'ROLLOVER', 'OTHERVEST', 'OTHERNONVEST')
ACCTTYPES = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')


class OFXElement(object):
    """
    Base class of validator/type converter for OFX 'element', i.e. SGML leaf
    node that contains text data.

    OFXElement instances store validation parameters relevant to a particular
    Aggregate subclass (e.g. maximum string length, decimal precision,
    required vs. optional, etc.) - they don't directly store the data
    itself (which lives in the __dict__ of an Aggregate instance).
    """
    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', False)
        self.required = required
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        """ Override in subclass """
        if args or kwargs:
            raise ValueError("Unknown args for '%s'- args: %r; kwargs: %r"
                            % (self.__class__.__name__, args, kwargs))

    def convert(self, value):
        """ Override in subclass """
        raise NotImplementedError


class OFXbool(OFXElement):
    mapping = {'Y': True, 'N': False}

    def convert(self, value):
        if value is None and not self.required:
            return None
        return self.mapping[value]

    def unconvert(self, value):
        if value is None and not self.required:
            return None
        return {v:k for k,v in self.mapping.items()}[value]

class OFXstr(OFXElement):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(OFXstr, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        if self.length is not None and len(value) > self.length:
            raise ValueError("'%s' is too long; max length=%s" % (value, self.length))
        return str(value)


class OneOf(OFXElement):
    def _init(self, *args, **kwargs):
        self.valid = set(args)
        super(OneOf, self)._init(**kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        if (value in self.valid):
            return value
        raise ValueError("'%s' is not OneOf %r" % (value, self.valid))


class OFXint(OFXElement):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(OFXint, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        value = int(value)
        if self.length is not None and value >= 10**self.length:
            raise ValueError('%s has too many digits; max digits=%s' % (value, self.length))
        return int(value)


class OFXdecimal(OFXElement):
    def _init(self, *args, **kwargs):
        precision = 2
        if args:
            precision = args[0]
            args = args[1:]
        self.precision = precision
        super(OFXdecimal, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        value = decimal.Decimal(value)
        precision = decimal.Decimal('0.' + '0'*(self.precision-1) + '1')
        value.quantize(precision)
        return value


class OFXdatetime(OFXElement):
    # Valid datetime formats given by OFX spec in section 3.2.8.2
    tz_re = re.compile(r'\[([-+]?\d{0,2}\.?\d*):?(\w*)\]')
    # strftime formats keyed by the length of the corresponding string
    formats = {18: '%Y%m%d%H%M%S.%f', 14: '%Y%m%d%H%M%S', 8: '%Y%m%d'}

    @classmethod
    def convert(cls, value):
        # If it's a datetime or None, don't touch it.
        if isinstance(value, datetime.datetime) or value is None:
            return value

        # Pristine copy of input for error reporting purposes
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        chunks = cls.tz_re.split(value)
        value = chunks.pop(0)
        if chunks:
            gmt_offset, tz_name = chunks[:2]
            # Some FIs *cough* IBKR *cough* write crap for the TZ offset
            if gmt_offset == '-':
                gmt_offset = '0'
            gmt_offset = int(decimal.Decimal(gmt_offset)*3600) # hours -> seconds
        else:
            gmt_offset = 0
        format = cls.formats[len(value)]
        try:
            value = datetime.datetime.strptime(value, format)
        except ValueError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                            (orig_value, cls.formats.values()))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=gmt_offset)
        return value

    @classmethod
    def unconvert(cls, value):
        """ Input datetime.datetime in local time; output str in GMT. """
        # Pristine copy of input for error reporting purposes
        orig_value = value

        try:
            # Transform to GMT
            value = time.gmtime(time.mktime(value.timetuple()))
            # timetuples don't have usec precision
            #value = time.strftime('%s[0:GMT]' % cls.formats[14], value)
            value = time.strftime(cls.formats[14], value)
        except:
            raise # FIXME
        return value


class Aggregate(object):
    """
    Base class of validator/type converter for OFX 'aggregate', i.e. SGML parent
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
                            % (self.__class__.__name__, kwargs.viewkeys()))

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

# 3-letter language codes
ISO639_2 = ('AAR', 'ABK', 'ACE', 'ACH', 'ADA', 'ADY', 'AFA', 'AFH', 'AFR',
            'AIN', 'AKA', 'AKK', 'SQI', 'ALE', 'ALG', 'ALT', 'AMH', 'ANG', 
            'ANP', 'APA', 'ARA', 'ARC', 'ARG', 'HYE', 'ARN', 'ARP', 'ART',
            'ARW', 'ASM', 'AST', 'ATH', 'AUS', 'AVA', 'AVE', 'AWA', 'AYM',
            'AZE', 'BAD', 'BAI', 'BAK', 'BAL', 'BAM', 'BAN', 'EUS', 'BAS', 
            'BAT', 'BEJ', 'BEL', 'BEM', 'BEN', 'BER', 'BHO', 'BIH', 'BIK', 
            'BIN', 'BIS', 'BLA', 'BNT', 'BOS', 'BRA', 'BRE', 'BTK', 'BUA',
            'BUG', 'BUL', 'MYA', 'BYN', 'CAD', 'CAI', 'CAR', 'CAT', 'CEB',
            'CEL', 'CHA', 'CHB', 'CHE', 'CHG', 'ZHO', 'CHK', 'CHM', 'CHN', 
            'CHO', 'CHP', 'CHR', 'CHV', 'CHY', 'CMC', 'COP', 'COR', 'COS',
            'CPE', 'CPF', 'CPP', 'CRE', 'CRH', 'CRP', 'CSB', 'CUS', 'CES',
            'DAK', 'DAN', 'DAR', 'DAY', 'DEL', 'DEN', 'DGR', 'DIN', 'DIV',
            'DOI', 'DRA', 'DSB', 'DUA', 'DUM', 'NLD', 'DZO', 'EFI', 'EGY',
            'EKA', 'ELX', 'ENG', 'ENM', 'EPO', 'EST', 'EWE', 'EWO', 'FAN',
            'FAO', 'FAT', 'FIJ', 'FIL', 'FIN', 'FON', 'FRA', 'FRM', 'FRO',
            'FRR', 'FRS', 'FRY', 'FUL', 'FUR', 'GAA', 'GAY', 'GBA', 'GEM',
            'KAT', 'GEZ', 'GIL', 'GLA', 'GLE', 'GLG', 'GLV', 'GMH', 'GOH', 
            'GON', 'GOR', 'GOT', 'GRB', 'GRC', 'ELL', 'GRN', 'GSW', 'GUJ', 
            'GWI', 'HAI', 'HAT', 'HAW', 'HEB', 'HER', 'HIL', 'HIM', 'HIN',
            'HIT', 'HMN', 'HMO', 'HRV', 'HSB', 'HUN', 'HUP', 'IBA', 'IBO',
            'ISL', 'IDO', 'III', 'IJO', 'ILE', 'ILO', 'INA', 'INC', 'IND',
            'INE', 'INH', 'IPK', 'IRA', 'IRO', 'ITA', 'JAV', 'JBO', 'JPN',
            'JPR', 'JRB', 'KAA', 'KAB', 'KAC', 'KAL', 'KAM', 'KAN', 'KAR',
            'KAS', 'KAW', 'KAZ', 'KBD', 'KHA', 'KHI', 'KHM', 'KHO', 'KIK',
            'KIN', 'KIR', 'KMB', 'KOK', 'KOM', 'KON', 'KOR', 'KOS', 'KPE',
            'KRC', 'KRL', 'KRO', 'KUA', 'KUM', 'KUR', 'KUT', 'LAD', 'LAH',
            'LAM', 'LAO', 'LAT', 'LAV', 'LEZ', 'LIM', 'LIN', 'LIT', 'LOL', 
            'LOZ', 'LTZ', 'LUA', 'LUB', 'LUG', 'LUI', 'LUN', 'LUO', 'LUS',
            'MKD', 'MAD', 'MAG', 'MAH', 'MAI', 'MAK', 'MAL', 'MAN', 'MRI', 
            'MAP', 'MAR', 'MAS', 'MSA', 'MDF', 'MDR', 'MEN', 'MGA', 'MIC', 
            'MIN', 'MIS', 'MKH', 'MLG', 'MLT', 'MNC', 'MNI', 'MNO', 'MOH', 
            'MON', 'MOS', 'MUL', 'MUN', 'MUS', 'MWL', 'MWR', 'MYN', 'MYV', 
            'NAH', 'NAI', 'NAP', 'NAV', 'NBL', 'NDE', 'NDO', 'NDS', 'NEP', 
            'NEW', 'NIA', 'NIC', 'NNO', 'NOB', 'NOG', 'NON', 'NOR', 'NQO', 
            'NSO', 'NUB', 'NWC', 'NYA', 'NYM', 'NYN', 'NYO', 'NZI', 'OCI',
            'OJI', 'ORI', 'ORM', 'OSA', 'OSS', 'OTA', 'OTO', 'PAA', 'PAG',
            'PAL', 'PAM', 'PAN', 'PAP', 'PEO', 'FAS', 'PHI', 'PHN', 'PLI',
            'POL', 'PON', 'POR', 'PRA', 'PRO', 'PUS', 'QUE', 'RAJ', 'RAP', 
            'RAR', 'ROA', 'ROH', 'ROM', 'RON', 'RUN', 'RUP', 'RUS', 'SAD',
            'SAG', 'SAH', 'SAI', 'SAL', 'SAM', 'SAN', 'SAS', 'SAT', 'SCN',
            'SCO', 'SEL', 'SEM', 'SGA', 'SGN', 'SHN', 'SID', 'SIN', 'SIO', 
            'SIT', 'SLA', 'SLO', 'SLV', 'SMA', 'SME', 'SMI', 'SMJ', 'SMN', 
            'SMO', 'SMS', 'SNA', 'SND', 'SNK', 'SOG', 'SOM', 'SON', 'SOT', 
            'SPA', 'SRD', 'SRN', 'SRP', 'SRR', 'SSA', 'SSW', 'SUK', 'SUN', 
            'SUS', 'SUX', 'SWA', 'SWE', 'SYC', 'SYR', 'TAH', 'TAI', 'TAM', 
            'TAT', 'TEL', 'TEM', 'TER', 'TET', 'TGK', 'TGL', 'THA', 'BOD', 
            'TIG', 'TIR', 'TIV', 'TKL', 'TLH', 'TLI', 'TMH', 'TOG', 'TON', 
            'TPI', 'TSI', 'TSN', 'TSO', 'TUK', 'TUM', 'TUP', 'TUR', 'TUT', 
            'TVL', 'TWI', 'TYV', 'UDM', 'UGA', 'UIG', 'UKR', 'UMB', 'UND', 
            'URD', 'UZB', 'VAI', 'VEN', 'VIE', 'VOL', 'VOT', 'WAK', 'WAL', 
            'WAR', 'WAS', 'CYM', 'WEN', 'WLN', 'WOL', 'XAL', 'XHO', 'YAO', 
            'YAP', 'YID', 'YOR', 'YPK', 'ZAP', 'ZBL', 'ZEN', 'ZHA', 'ZND',
            'ZUL', 'ZUN', 'ZXX', 'ZZA') 

# Currency codes
ISO4217 = ('AE', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN',
           'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BOV',
           'BRL', 'BSD', 'BTN', 'BWP', 'BYR', 'BZD', 'CAD', 'CDF', 'CHE', 'CHF',
           'CHW', 'CLF', 'CLP', 'CNY', 'COP', 'CO', 'CRC', 'CUC', 'CUP', 'CVE',
           'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 'EEK', 'EGP', 'ERN', 'ETB', 'EUR',
           'FJD', 'FKP', 'GBP', 'GEL', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD',
           'HKD', 'HNL', 'HRK', 'HTG', 'HUF', 'IDR', 'ILS', 'INR', 'IQD', 'IRR',
           'ISK', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW',
           'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LVL',
           'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRO', 'MUR',
           'MVR', 'MWK', 'MXN', 'MXV', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK',
           'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG',
           'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR', 'SDG', 'SEK',
           'SGD', 'SHP', 'SLL', 'SOS', 'SRD', 'STD', 'SVC', 'SYP', 'SZL', 'THB',
           'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TWD', 'TZS', 'UAH', 'UGX',
           'USD', 'USN', 'USS', 'UYI', 'UY', 'UZS', 'VEF', 'VND', 'VUV', 'WST',
           'XAF', 'XAG', 'XA', 'XBA', 'XBB', 'XBC', 'XBD', 'XCD', 'XDR', 'XF',
           'XOF', 'XPD', 'XPF', 'XPT', 'XTS', 'XXX', 'YER', 'ZAR', 'ZMK', 'ZWL')

# Country codes
ISO3166_1a3 = ('ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ANT', 'ARE',
               'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 'AZE', 
               'BDI', 'BEL', 'BEN', 'BFA', 'BGD', 'BGR', 'BHR', 'BHS', 'BIH',
               'BLM', 'BLR', 'BLZ', 'BM', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN',
               'BVT', 'BWA', 'CAF', 'CAN', 'CCK', 'CHE', 'CHL', 'CHN', 'CIV',
               'CMR', 'COD', 'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB',
               'CXR', 'CYM', 'CYP', 'CZE', 'DE', 'DJI', 'DMA', 'DNK', 'DOM',
               'DZA', 'EC', 'EGY', 'ERI', 'ESH', 'ESP', 'EST', 'ETH', 'FIN',
               'FJI', 'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY', 
               'GHA', 'GIB', 'GIN', 'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD', 
               'GRL', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG', 'HMD', 'HND', 'HRV',
               'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IOT', 'IRL', 'IRN', 'IRQ',
               'ISL', 'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'JPN', 'KAZ', 'KEN',
               'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR',
               'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LT', 'LUX', 'LVA', 'MAC', 
               'MAF', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD',
               'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR',
               'MTQ', 'MUS', 'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK',
               'NGA', 'NIC', 'NI', 'NLD', 'NOR', 'NPL', 'NR', 'NZL', 'OMN', 
               'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRI',
               'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'RE', 'RO', 'RUS',
               'RWA', 'SA', 'SDN', 'SEN', 'SGP', 'SGS', 'SHN', 'SJM', 'SLB', 
               'SLE', 'SLV', 'SMR', 'SOM', 'SPM', 'SRB', 'STP', 'SUR', 'SVK',
               'SVN', 'SWE', 'SWZ', 'SYC', 'SYR', 'TCA', 'TCD', 'TGO', 'THA', 
               'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV',
               'TWN', 'TZA', 'UGA', 'UKR', 'UMI', 'URY', 'USA', 'UZB', 'VAT',
               'VCT', 'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM',
               'ZAF', 'ZMB', 'ZWE')

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

    mfassetclass = []
    fimfassetclass = []


class MFASSETCLASS(Aggregate):
    assetclass = OneOf(*ASSETCLASSES)
    percent = OFXdecimal()


class FIMFASSETCLASS(Aggregate):
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


### UTILITIES
def fixpath(path):
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path

OFXv1 = ('102', '103')
OFXv2 = ('200', '203', '211')

APPIDS = ('QWIN', # Quicken for Windows
            'QMOFX', # Quicken for Mac
            'QBW', # QuickBooks for Windows
            'QBM', # QuickBooks for Mac
            'Money', # MSFT Money
            'Money Plus', # MSFT Money Plus
            'PyOFX', # Custom
)

APPVERS = ('1500', # Quicken 2006/ Money 2006
            '1600', # Quicken 2007/ Money 2007/ QuickBooks 2006
            '1700', # Quicken 2008/ Money Plus/ QuickBooks 2007
            '1800', # Quicken 2009/ QuickBooks 2008
            '1900', # Quicken 2010/ QuickBooks 2009
            '2000', # QuickBooks 2010
            '9999', # Custom
)


# 2-letter country codes for numbering agencies (used to construct ISINs)
# Swiped from
# http://code.activestate.com/recipes/498277-isin-validator/
numberingAgencies = {'BE': ('Euronext - Brussels', 'Belgium'),
'FR': ('Euroclear France', 'France'),
'BG': ('Central Depository of Bulgaria', 'Bulgaria'),
'VE': ('Bolsa de Valores de Caracas, C.A.', 'Venezuela'),
'DK': ('VP Securities Services', 'Denmark'),
'HR': ('SDA - Central Depository Agency of Croatia', 'Croatia'),
'DE': ('Wertpapier-Mitteilungen', 'Germany'),
'JP': ('Tokyo Stock Exchange', 'Japan'),
'H': ('KELER', 'Hungary'),
'HK': ('Hong Kong Exchanges and Clearing Ltd', 'Hong Kong'),
'JO': ('Securities Depository Center of Jordan', 'Jordan'),
'BR': ('Bolsa de Valores de Sao Paulo - BOVESPA', 'Brazil'),
'XS': ('Clearstream Banking', 'Clearstream'),
'FI': ('Finnish Central Securities Depository Ltd', 'Finland'),
'GR': ('Central Securities Depository S.A.', 'Greece'),
'IS': ('Icelandic Securities Depository', 'Iceland'),
'R': ('The National Depository Center, Russia', 'Russia'),
'LB': ('Midclear S.A.L.', 'Lebanon'),
'PT': ('Interbolsa - Sociedade Gestora de Sistemas de Liquidação e Sistemas Centralizados de Valores', 'Portugal'),
'NO': ('Verdipapirsentralen (VPS) ASA', 'Norway'),
'TW': ('Taiwan Stock Exchange Corporation', 'Taiwan, Province of China'),
'UA': ('National Depository of Ukraine', 'Ukraine'),
'TR': ('Takasbank', 'Turkey'),
'LK': ('Colombo Stock Exchange', 'Sri Lanka'),
'LV': ('OMX - Latvian Central Depository', 'Latvia'),
'L': ('Clearstream Banking', 'Luxembourg'),
'TH': ('Thailand Securities Depository Co., Ltd', 'Thailand'),
'NL': ('Euronext Netherlands', 'Netherlands'),
'PK': ('Central Depository Company of Pakistan Ltd', 'Pakistan'),
'PH': ('Philippine Stock Exchange, Inc.', 'Philippines'),
'RO': ('The National Securities Clearing Settlement and Depository Corporation', 'Romania'),
'EG': ('Misr for Central Clearing, Depository and Registry (MCDR)', 'Egypt'),
'PL': ('National Depository for Securities', 'Poland'),
'AA': ('ANNA Secretariat', 'ANNAland'),
'CH': ('Telekurs Financial Ltd.', 'Switzerland'),
'CN': ('China Securities Regulatory Commission', 'China'),
'CL': ('Deposito Central de Valores', 'Chile'),
'EE': ('Estonian Central Depository for Securities', 'Estonia'),
'CA': ('The Canadian Depository for Securities Ltd', 'Canada'),
'IR': ('Tehran Stock Exchange Services Company', 'Iran'),
'IT': ('Ufficio Italiano dei Cambi', 'Italy'),
'ZA': ('JSE Securities Exchange of South Africa', 'South Africa'),
'CZ': ('Czech National Bank', 'Czech Republic'),
'CY': ('Cyprus Stock Exchange', 'Cyprus'),
'AR': ('Caja de Valores S.A.', 'Argentina'),
'A': ('Australian Stock Exchange Limited', 'Australia'),
'AT': ('Oesterreichische Kontrollbank AG', 'Austria'),
'IN': ('Securities and Exchange Board of India', 'India'),
'CS': ('Central Securities Depository A.D. Beograd', 'Serbia & Montenegro'),
'CR': ('Central de Valores - CEVAL', 'Costa Rica'),
'IE': ('The Irish Stock Exchange', 'Ireland'),
'ID': ('PT. Kustodian Sentral Efek Indonesia (Indonesian Central Securities Depository (ICSD))', 'Indonesia'),
'ES': ('Comision Nacional del Mercado de Valores (CNMV)', 'Spain'),
'PE': ('Bolsa de Valores de Lima', 'Per'),
'TN': ('Sticodevam', 'Tunisia'),
'PA': ('Bolsa de Valores de Panama S.A.', 'Panama'),
'SG': ('Singapore Exchange Limited', 'Singapore'),
'IL': ('The Tel Aviv Stock Exchange', 'Israel'),
'US': ("Standard & Poor's - CUSIP Service Bureau", 'USA'),
'MX': ('S.D. Indeval SA de CV', 'Mexico'),
'SK': ('Central Securities Depository SR, Inc.', 'Slovakia'),
'KR': ('Korea Exchange - KRX', 'Korea'),
'SI': ('KDD Central Securities Clearing Corporation', 'Slovenia'),
'KW': ('Kuwait Clearing Company', 'Kuwait'),
'MY': ('Bursa Malaysia', 'Malaysia'),
'MO': ('MAROCLEAR S.A.', 'Morocco'),
'SE': ('VPC AB', 'Sweden'),
'GB': ('London Stock Exchange', 'United Kingdom')}

def cusipChecksum(base):
    """
    Compute the check digit for a base Committee on Uniform Security
    Identification Procedures (CUSIP) securities identifier.
    Input an 8-digit alphanum str, output a single-char str.

    http://goo.gl/4TeWl
    """
    def encode(index, char):
        num = {'*': 36, '@': 37, '#': 38}.get(char, int(char, 36))
        return str(num * 2) if index % 2 else str(num)

    assert len(base) == 8
    for badLetter in 'IO':
        assert badLetter not in base
    check = ''.join([encode(index, char) for index, char in enumerate(base)])
    check = sum([int(digit) for digit in check])
    return str((10 - (check % 10)) % 10)

def sedolChecksum(base):
    """
    Stock Exchange Daily Official List (SEDOL)
    http://goo.gl/HxFWL
    """
    weights = (1, 3, 1, 7, 3, 9)

    assert len(base) == 6
    for badLetter in 'AEIO':
        assert badLetter not in base
    check = sum([int(char, 36) * weights[n] for n, char in enumerate(base)])
    return str((10 - (check % 10)) % 10)

def isinChecksum(base):
    """
    Compute the check digit for a base International Securities Identification
    Number (ISIN).  Input an 11-char alphanum str, output a single-char str.

    http://goo.gl/8kPzD
    """
    assert len(base) == 11
    assert base[:2] in numberingAgencies.keys()
    check = ''.join([int(char, 36) for char in base])
    check = check[::-1] # string reversal
    check = ''.join([d if n%2 else str(int(d)*2) for n, d in enumerate(check)])
    return str((10 - sum([int(d) for d in check]) % 10) % 10)

def cusip2isin(cusip, nation=None):
    nation = nation or 'US'
    assert len(cusip) == 9
    assert CUSIPchecksum(cusip[:8]) == cusip[9]
    base = nation + cusip
    return base + ISINchecksum(base)

def sedol2isin(sedol, nation=None):
    nation = nation or 'GB'
    assert len(sedol) == 7
    assert SEDOLchecksum(sedol[:6]) == sedol[6]
    base = nation + sedol.zfill(9)
    return base + ISINchecksum(base)

def settleDate(dt):
    """
    Given a trade date (or datetime), return the trade settlement date(time)
    """
    def nextBizDay(dt):
        stop = False
        while not stop:
            dt += datetime.timedelta(days=1)
            if dt.weekday() in (5, 6) or dt in NYSEcalendar.holidays(dt.year):
                stop = False
            else:
                stop = True
        return dt

    #print dt
    for n in range(3):
        dt = nextBizDay(dt)
    #print dt
    return dt


class NYSEcalendar(object):
    """
    The Board has determined that the Exchange will not be open for business on
        New Year's Day,
        Martin Luther King, Jr. Day,
        Washington's Birthday,
        Good Friday,
        Memorial Day,
        Independence Day,
        Labor Day,
        Thanksgiving Day
        and Christmas Day.
    Martin Luther King, Jr. Day, Washington's Birthday and Memorial Day will be
    celebrated on the third Monday in January, the third Monday in February
    and the last Monday in May, respectively

    The Exchange Board has also determined that, when any holiday observed by
    the Exchange falls on a Saturday, the Exchange will not be open for
    business on the preceding Friday and when any holiday observed by the
    Exchange falls on a Sunday, the Exchange will not be open for business on
    the succeeding Monday, unless unusual business conditions exist,
    such as the ending of a monthly or the yearly accounting period.
    """
    _cal = calendar.Calendar()

    @classmethod
    def _weekdays(cls, year, month, weekday):
        """
        Filter datetime.dates in (year, month) for a given weekday.
        """
        def weekdayTest(days):
            return (days[0] > 0) and (days[1] == weekday)
        return [datetime.date(year, month, day) \
                for (day, wkday) in itertools.ifilter(weekdayTest,
                                        cls._cal.itermonthdays2(year, month))]

    @classmethod
    def mondays(cls, year, month):
        return cls._weekdays(year, month, weekday=0)

    @classmethod
    def thursdays(cls, year, month):
        return cls._weekdays(year, month, weekday=3)

    @classmethod
    def holidays(cls, year):
        hols = [datetime.date(year, 7, 4), # Independence Day
                datetime.date(year, 12, 25), # Christmas
                cls.mondays(year, 1)[2], # MLK Day
                findEaster(year) - datetime.timedelta(days=2), # Good Friday
                cls.mondays(year, 2)[2], # Washington's Birthday
                cls.mondays(year, 5)[-1], # Memorial Day
                cls.mondays(year, 9)[0], # Labor Day
                cls.thursdays(year, 11)[-1], # Thanksgiving
        ]
        newYearsDay = datetime.date(year, 1, 1)
        if newYearsDay.weekday() != 5:
            # If New Year's Day falls on a Saturday, then it would get moved
            # back to the preceding Friday, except that would be 12/31, which
            # is the close of the monthly and annual accounting cycle... so
            # in that case, the holiday just gets skipped instead.
            hols.append(newYearsDay)
        hols.sort()
        return hols


def findEaster(year):
    """
    Copyright (c) 2003  Gustavo Niemeyer <niemeyer@conectiva.com>
    The code is licensed under the PSF license.

    This method was ported from the work done by GM Arts,
    on top of the algorithm by Claus Tondering, which was
    based in part on the algorithm of Ouding (1940), as
    quoted in "Explanatory Supplement to the Astronomical
    Almanac", P.  Kenneth Seidelmann, editor.

    Edited by csingley to "de-modulize" the function to fit into pyofx,
    and to remove unused Easter calculation methods.

    This algorithm implements the revised method of easter calculation,
    in Gregorian calendar, valid in years 1583 to 4099.

    More about the algorithm may be found at:
    http://users.chariot.net.au/~gmarts/eastalg.htm
    and
    http://www.tondering.dk/claus/calendar.html
    """
    # g - Golden year - 1
    # c - Century
    # h - (23 - Epact) mod 30
    # i - Number of days from March 21 to Paschal Full Moon
    # j - Weekday for PFM (0=Sunday, etc)
    # p - Number of days from March 21 to Sunday on or before PFM
    #     (-6 to 28)

    y = year
    g = y % 19
    e = 0

    # New method (i.e. EASTER_WESTERN)
    c = y/100
    h = (c-c/4-(8*c+13)/25+19*g+15)%30
    i = h-(h/28)*(1-(h/28)*(29/(h+1))*((21-g)/11))
    j = (y+y/4+i+2-c+c/4)%7

    # p can be from -6 to 56 corresponding to dates 22 March to 23 May
    # (later dates apply to method 2, although 23 May never actually occurs)
    p = i-j+e
    d = 1+(p+27+(p+6)/40)%31
    m = 3+(p+26)/30
    return datetime.date(y,m,d)


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

