#!/usr/bin/env python3
import sys
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

import converters
from utilities import _, OFXv1, OFXv2, prettify


class OFXParser(ET.ElementTree):
    v1Header = re.compile(r"""\s*
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

    v2Header = re.compile(r"""(<\?xml\s+
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

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source)
        source = source.read()

        ### First parse OFX header
        v1Header = self.v1Header.match(source)
        if v1Header:
            # OFXv1
            header = v1Header.groupdict()
            # Sanity check
            try:
                assert header['OFXHEADER'] == '100'
                assert header['DATA'] == 'OFXSGML'
                assert header['VERSION'] in OFXv1
                assert header['SECURITY'] in ('NONE', 'TYPE1')
                assert header['ENCODING'] in ('UNICODE', 'USASCII')
            except AssertionError:
                raise ParseError('Malformed OFX header %s' % str(header))
            source = source[v1Header.end():]
        else:
            # OFXv2
            v2Header = self.v2Header.match(source)
            if not v2Header:
                raise ParseError('Missing OFX Header')
            header = v2Header.groupdict()
            # Sanity check
            try:
                assert header['OFXHEADER'] == '200'
                assert header['VERSION'] in OFXv2
                assert header['SECURITY'] in ('NONE', 'TYPE1')
            except AssertionError:
                raise ParseError('Malformed OFX header %s' % str(header))
            source = source[v2Header.end():]

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


def main():
    from argparse import ArgumentParser

    argparser = ArgumentParser()
    argparser.add_argument('file')
    args = argparser.parse_args()

    ofxparser = OFXParser()
    ofxparser.parse(_(args.file))

    stmt = ofxparser.response.statements[0]
    if isinstance(stmt, (STMT, CCSTMT)):
        tranlist = stmt.banktranlist
    elif isinstance(stmt, INVSTMT):
        tranlist = stmt.invtranlist
    else:
        raise ValueError('%s not an instance of (STMT, CCSTMT, INVSTMT)' % stmt)
    print(tranlist)


if __name__ == '__main__':
    main()
