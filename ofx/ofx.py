#!/usr/bin/env python3
import datetime
import uuid
from xml.etree.cElementTree import Element, SubElement, tostring
from collections import defaultdict, OrderedDict
import contextlib
from urllib.request import Request, urlopen, HTTPError
from urllib.parse import urlparse
from io import StringIO
import os
import re
import xml.etree.ElementTree as ET
from configparser import SafeConfigParser
from getpass import getpass

import converters

### UTILITIS
def fixpath(path):
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path


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
        accttype = converters.OneOf(*converters.ACCTTYPES).convert(accttype)
        self._acct['ACCTTYPE'] = converters.OneOf(*converters.ACCTTYPES).convert(accttype)

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
            SubElement(tran, 'DTSTART').text = converters.DateTime.unconvert(dtstart)
        if dtend:
            SubElement(tran, 'DTEND').text = converters.DateTime.unconvert(dtend)
        SubElement(tran, 'INCLUDE').text = converters.Boolean().unconvert(inctran)
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
        oo.text = converters.Boolean().unconvert(False)
        return oo

    def incpos(self, dtasof, incpos):
        pos = Element('INCPOS')
        if dtasof:
            SubElement(pos, 'DTASOF').text = converters.DateTime.unconvert(dtasof)
        SubElement(pos, 'INCLUDE').text = converters.Boolean().unconvert(incpos)
        return pos

    def incbal(self, incbal):
        bal = Element('INCBAL')
        bal.text = converters.Boolean().unconvert(incbal)
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
        SubElement(sonrq, 'DTCLIENT').text = converters.DateTime.unconvert(datetime.datetime.now())
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
        SubElement(profrq, 'DTPROFUP').text = converters.DateTime.unconvert(datetime.date(1990,1,1))
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
        parser = OFXTreeBuilder(element_factory=OFXElement)
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
                self.start(tag, attrs={})
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
                    self.start(tag, attrs={})
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


class OFXElement(ET.Element):
    """ """
    currencyTags = ()
    origcurrencyAggregates = (converters.STMTTRN, converters.INVBUY,
                            converters.INVSELL, converters.INCOME,
                            converters.INVEXPENSE, converters.MARGININTEREST,
                            converters.REINVEST, converters.RETOFCAP)
    def convert(self):
        """ """
        converterClass = getattr(converters, self.tag)
        assert issubclass(converterClass, converters.Aggregate)
        attributes = self._flatten()

        if issubclass(converterClass, converters.ORIGCURRENCY):
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
                    stmt.trnuid = converters.Unicode(36).convert(trnrs.find('TRNUID').text)
                    stmt.status = trnrs.find('STATUS').convert()
                    cltcookie = trnrs.find('CLTCOOKIE')
                    if cltcookie is not None:
                        stmt.cltcookie = converters.Unicode(36).convert(cltcookie.text)
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
        self.dtasof = converters.DateTime.convert(dtasof)

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
        self.dtstart = converters.DateTime.convert(dtstart.text)
        self.dtend = converters.DateTime.convert(dtend.text)
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
    main_config = fixpath(os.path.join(os.path.dirname(__file__), 'main.cfg'))

    def __init__(self):
        SafeConfigParser.__init__(self)

    def read(self, filenames=None):
        # Load main config
        self.readfp(open(self.main_config))
        # Then load user configs (defaults to main.cfg [global] config: value)
        filenames = filenames or fixpath(self.get('global', 'config'))
        return SafeConfigParser.read(self, filenames)

    @property
    def fi_index(self):
        sections = self.sections()
        sections.remove('global')
        return sections

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

    #print(accts)

    # Use dummy password for dummy request
    if args.dry_run:
        password = 'T0PS3CR3T'
    else:
        password = getpass()

    # Statement parameters
    d = vars(args)
    # convert dtstart/dtend/dtasof from str to datetime
    kwargs = {k:converters.DateTime.convert(v) for k,v in d.items() if k.startswith('dt')}
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

