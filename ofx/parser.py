#!/usr/bin/env python
import sys
import re
import xml.etree.ElementTree as ET
from collections import Counter

import converters
from utilities import _, OFXv1, OFXv2, prettify


if sys.version_info < (2, 7):
    raise RuntimeError('ofx.parser library requires Python v2.7+')


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
            source = open(source, 'rb')
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
            parser = OFXTreeBuilder(element_factory=OFXElement)
        else:
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
            parser = ET.XMLTreeBuilder(element_factory=OFXElement)

        ### Then parse tag soup into tree of Elements
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
        self.tagCount = Counter()
        self.closeTagCount = Counter()
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
            # HACK: ET.TreeBuilder.end() raises an AssertionError for
            # internal errors generated by ET.TreeBuilder._flush(),
            # but also for ending tag mismatches, which are problems
            # with the data rather than the parser.  We want to pass
            # on the former but handle the latter; however, the only
            # difference between the two is in the error message.
            if 'end tag mismatch' in err.message:
                raise ParseError(err.message)
            else:
                raise


class OFXElement(ET.Element):
    """ """
    def convert(self):
        """ """
        return getattr(converters, self.tag)(**self._flatten())

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
            # FIXME - probably shouldn't just throw this info away
            mfassetclass = sec.find('MFASSETCLASS')
            if mfassetclass:
                sec.remove(mfassetclass)
            fimfassetclass = sec.find('FIMFASSETCLASS')
            if fimfassetclass:
                sec.remove(fimfassetclass)
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

    dtstart = None
    dtend = None

    ballist = []

    def __init__(self, stmtrs):
        """ Initialize with *STMTRS Element """
        self.curdef = stmtrs.find('CURDEF').text
        self.acctfrom = stmtrs.find(self._acctTag).convert()
        self.process(stmtrs)

    def process(self, stmtrs):
        raise NotImplementedError

    def _processBALLIST(self, ballist):
        return [bal.convert() for bal in ballist]

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))


class STMT(BaseSTMT):
    ledgerbal = None
    availbal = None

    banktranlist = []

    _acctTag = 'BANKACCTFROM'

    @property
    def bankacctfrom(self):
        return self.acctfrom

    def process(self, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)

            self.dtStart = converters.DateTime.convert(dtstart.text)
            self.dtEnd = converters.DateTime.convert(dtend.text)
            self.banktranlist = [tran.convert() for tran in tranlist]

        # LEDGERBAL - mandatory
        self.ledgerbal = stmtrs.find('LEDGERBAL').convert()

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            self.availbal = availbal.convert()

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.ballist = self._processBALLIST(ballist)

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


class INVSTMT(BaseSTMT):
    dtasof = None

    invtranlist = []
    invposlist = []
    invbal = None

    _acctTag = 'INVACCTFROM'

    @property
    def invacctfrom(self):
        return self.acctfrom

    def process(self, invstmtrs):
        dtasof = invstmtrs.find('DTASOF').text
        self.dtasof = converters.DateTime.convert(dtasof)

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            self.dtStart = converters.DateTime.convert(dtstart.text)
            self.dtEnd = converters.DateTime.convert(dtend.text)
            for trn in tranlist:
                self.invtranlist.append(trn.convert())

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            for pos in poslist:
                self.invposlist.append(pos.convert())

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal is not None:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist is not None:
                invbal.remove(ballist)
                self.ballist = self._processBALLIST(ballist)
            # Now we can flatten the rest of INVBAL
            self.invbal = invbal.convert()

        # Unsupported subaggregates
        for tag in ('INVOOLIST', 'INV401K', 'INV401KBAL', 'MKTGINFO'):
            child = invstmtrs.find(tag)
            if child:
                invstmtrs.remove


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
        print stmt.banktranlist
    elif isinstance(stmt, INVSTMT):
        print stmt.invtranlist
    else:
        raise ValueError('%s not an instance of (STMT, CCSTMT, INVSTMT)' % stmt)


if __name__ == '__main__':
    main()