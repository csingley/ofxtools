#!/usr/bin/env python2
import os
import xml.etree.cElementTree as ET

import valid

class OFXParser(object):
    """ """
    BANKTRANLISTitem = valid.BANKTRANLISTitem
    SECLISTitem = valid.SECLISTitem
    INVTRANLISTitem = valid.INVTRANLISTitem
    POSLISTitem = valid.POSLISTitem

    def __init__(self, verbose=False):
        """ """
        self.reset()
        self.verbose = verbose

    def reset(self):
        self.header = None
        self.tree = ET.ElementTree()
        self.bank_transactions = None
        self.bank_balance = None
        self.bank_balance_available = None
        self.creditcard_transactions = None
        self.securities = None
        self.invstmtrs_preamble = None
        self.invtranlist_preamble = None
        self.investment_transactions = None
        self.positions = None
        self.investment_balances = None

    def parse(self, source):
        """ """
        if not hasattr(source, 'read"'):
            source = open(source, 'rb')
        self.header, source = self.unwrapOFX(source)
        # Mark position where markup begins
        breakbeat = source.tell()
        with source as s:
            try:
                # If all tags are closed explicitly, expat will work
                parser = ET.XMLParser()
                root = self.tree.parse(s, parser)
            except SyntaxError:
                # Fall back to sgmlop if available (it's faster), else sgmllib.
                try:
                    parser = OFXTreeBuilder_sgmlop(verbose=self.verbose)
                except ImportError:
                    parser = OFXTreeBuilder(verbose=self.verbose)
                # expat started playing; rewind
                s.seek(breakbeat)
                root = self.tree.parse(s, parser)

        # STMTRS
        stmtrs = root.find('.//STMTRS')
        if stmtrs:
            self.stmtrs_preamble, self.tranlist_preamble, self.bank_transactions, self.bank_balance, self.bank_balance_available = self.parse_STMTRS(stmtrs)

        # CCSTMTRS
        ccstmtrs = root.find('.//CCSTMTRS')
        if ccstmtrs:
            self.ccstmtrs_preamble, self.cctranlist_preamble, self.creditcard_transactions, self.creditcard_balance, self.creditcard_balance_available = self.parse_STMTRS(ccstmtrs)

        # SECLIST
        seclist = root.find('.//SECLIST')
        if seclist:
            def init_sec(element):
                # Strip out SECID so it won't run through parse_SECID()...
                secinfo = element.find('SECINFO')
                secid = secinfo.find('SECID')
                secinfo.remove(secid)
                # ...then parse the rest of the xxxINFO naively
                secattr = self.parse_element(element)
                # Merge in SECID (Double check for namespace collisions)
                secid_attr = dict([(child.tag.lower(), child.text) for child in secid])
                for key in secid_attr.keys():
                    assert key not in secattr.keys()
                secattr.update(valid.SECID.to_python(secid_attr))
                # Merge in security type
                assert 'type' not in secattr.keys()
                secattr['type'] = self.SECLISTitem.to_python(element.tag)[:-4]
                security = Security(**secattr)
                return (secattr['uniqueidtype'], secattr['uniqueid']), security
            self.securities = dict([init_sec(sec) for sec in seclist])

        # INVSTMTRS
        invstmtrs = root.find('.//INVSTMTRS')
        if invstmtrs:
            # Copy the STMTRS aggregate without the TRANLIST, so we can parse
            #  the preamble using default method (recursing into ACCTFROM)
            invstmtrs_clone = self._clone(invstmtrs, num_children=3)
            self.invstmtrs_preamble = self.parse_element(invstmtrs_clone)
            # INVTRANLIST
            invtranlist = invstmtrs.find('INVTRANLIST')
            if invtranlist:
                self.invtranlist_preamble = self.parse_element(invtranlist, recurse=False)
                def parse_tran(element):
                    # Parse the body of the transaction
                    tranattr = self.parse_element(element)
                    # Merge in transaction type
                    assert type not in tranattr.keys()
                    tranattr['type'] = self.INVTRANLISTitem.to_python(element.tag)
                    return InvTransaction(**tranattr)
                self.investment_transactions = [parse_tran(tran) for tran in invtranlist[2:]]

            # INVPOSLIST
            invposlist = invstmtrs.find('INVPOSLIST')
            if invposlist:
                def parse_item(element):
                    # Parse body
                    attr = self.parse_element(element)
                    # Merge in type
                    assert type not in attr.keys()
                    attr['type'] = self.POSLISTitem.to_python(element.tag)[3:]
                    return Position(**attr)
                self.positions = [parse_item(pos) for pos in invposlist]

            # INVBAL
            # FIXME - BALLIST is silently dropped
            invbal = invstmtrs.find('INVBAL')
            if invbal:
                # Strip off BALLIST and parse it
                ballist = invbal.find('BALLIST')
                if ballist:
                    invbal.remove(ballist)
                    bals = [self.parse_element(bal) for bal in ballist]
                else:
                    bals = None
                # Parse the rest of INVBAL
                attr = self.parse_element(invbal)
                self.investment_balances = InvBalance(**attr)

    def parse_STMTRS(self, stmtrs):
        # Copy the STMTRS aggregate without the TRANLIST, so we can parse
        #  the preamble using default method (recursing into ACCTFROM)
        stmtrs_clone = self._clone(stmtrs, num_children=2)
        stmtrs_preamble = self.parse_element(stmtrs_clone)
        # BANKTRANLIST
        banktranlist = stmtrs.find('BANKTRANLIST')
        if banktranlist:
            tranlist_preamble = self.parse_element(banktranlist, recurse=False)
            def parse_tran(element):
                # Parse the body of the transaction
                tranattr = self.parse_element(element)
                # Merge in transaction type
                assert type not in tranattr.keys()
                tranattr['type'] = self.BANKTRANLISTitem.to_python(element.tag)
                return Transaction(**tranattr)
            transactions = [parse_tran(tran) for tran in banktranlist[2:]]
        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        balance = self.parse_element(ledgerbal)
        # AVAILBAL
        availbal = stmtrs.find('LEDGERBAL')
        if availbal:
            balance_available = self.parse_element(availbal)
        # BALLIST
        # FIXME
        pass

        return stmtrs_preamble, tranlist_preamble, transactions, balance, balance_available

    def parse_element(self, element, recurse=True):
        """
        Default parsing method if nothing more specific overrides.
        Relies on the fact that OFX aggregates contain no data.
        """
        aggregates = {}
        leaves = {}
        for child in element:
            tag = child.tag
            data = child.text
            if data is not None:
                data = data.strip()
            if data:
                # element is a leaf element.
                assert tag not in leaves
                leaves[tag.lower()] = data
            elif recurse:
                # element is an aggregate and we haven't turned off recursion.
                # dispatch parse method; fallback to default (recurse here).
                parseMethod = getattr(self, 'parse_%s' % tag, self.parse_element)
                assert tag not in aggregates
                aggregates.update(parseMethod(child))
        # Validate leaves; aggregates are already validated by parse method.
        validation_schema = getattr(valid, element.tag)
        results = validation_schema.to_python(leaves)
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggregates.keys():
            assert key not in leaves.keys()
        results.update(aggregates)
        return results

    def parse_SECID(self, element):
        # Validate
        results = self.parse_element(element)
        # Transform to Security instance
        sec = self.securities[(results['uniqueidtype'], results['uniqueid'])]
        return {'secid': sec}

    def _clone(self, element, num_children=-1):
        """ """
        clone = ET.Element(element.tag)
        clone.text = element.text
        for child in element[:num_children]:
            clone.append(child)
        return clone

    def unwrapOFX(self, source):
        """ Pass in an open file-like object """
        def next_nonempty_line(source):
            FOUND_CONTENT = False
            while not FOUND_CONTENT:
                line = source.readline()
                # Per Python docs, for str.readline(), 'An empty string is
                #  returned only when EOF is encountered immediately.'
                if line == '':
                    raise EOFError("Source is empty")
                line = line.strip()
                if line:
                    FOUND_CONTENT = True
            return line

        def validateOFXv1Header(line, field):
            try:
                key, value = line.split(':')
                assert key == field
            except ValueError:
                # If split() doesn't yield a duple
                raise ValueError("Malformed OFX header '%s'" % line)
            except AssertionError:
                raise ValueError("Expecting OFX header field '%s' not '%s'" % (field, key))
            return key.strip(), value.strip()

        line1 = next_nonempty_line(source)
        if line1.startswith('OFXHEADER'):
            # OFXv1
            # Header is 9 lines of flat text (not markup) that we strip
            header_key, header_version = validateOFXv1Header(line1, 'OFXHEADER')
            header = dict([validateOFXv1Header(source.readline(), f) \
                    for f in valid.HEADER_FIELDS[header_version]])
            header[header_key] = header_version
            # Sanity check
            assert header['DATA'] == 'OFXSGML'
            assert header['VERSION'] in valid.OFXv1
        elif line1.startswith('<?xml'):
            #OFXv2
            # OFX declaration is the next line of content
            ofx_decl = next_nonempty_line(source)
            assert ofx_decl.endswith('?>')
            args = ofx_decl[:-3].split(' ')[1:]
            header = dict([arg.split('=') for arg in args])
            # Sanity check
            assert header['VERSION'] in valid.OFXv2
        else:
            raise ValueError("Malformed OFX header '%s'" % line1)

        return header, source

    #def sgml2xml(self, sgmlstr, version='102', sx=None):
        #""" """
        #version = str(version)
        #if version not in valid.OFXv1:
            #raise ValueError('version must be one of %s' % str(valid.OFXv1))
        #if version == '102':
            ## Use the DTD for OFXv103
            #version = '103'
        #spec = os.path.join(INSTALL_DIR, 'spec',version)
        #if not os.path.isdir(spec):
            #raise RuntimeError("Can't find OFXv%s spec at %s" % (version, spec))
        #sx = sx or self.world_sx or self.module_sx
        #if not sx:
            #raise RuntimeError("Can't find sx")
        #SX = Popen([sx, '-D%s' % spec], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        #xmlstr, stderr = SX.communicate(sgmlstr)
        #return xmlstr

from sgmllib import SGMLParser
class OFXTreeBuilder(SGMLParser):
    def __init__(self, verbose=False):
        self.__builder = ET.TreeBuilder()
        SGMLParser.__init__(self)
        self.inside_data = False
        self.latest_starttag = None
        self.verbose = verbose

    def feed(self, data):
        return SGMLParser.feed(self, data)

    def close(self):
        SGMLParser.close(self)
        return self.__builder.close()

    def unknown_starttag(self, tag, attrib):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "starttag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if self.verbose:
            msg = "starttag opening '%s'" % tag
            print msg
        self.__builder.start(tag, attrib)
        self.latest_starttag = tag

    def unknown_endtag(self, tag):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "endtag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if tag != self.latest_starttag:
            if self.verbose:
                msg = "endtag closing '%s'" % tag
                print msg
            self.__builder.end(tag)

    def handle_data(self, text):
        text = text.strip('\f\n\r\t\v') # Strip whitespace, except space char
        if text:
            if self.verbose:
                msg = "handle_data adding data '%s'" % text
                print msg
            self.inside_data = True
            self.__builder.data(text)

class OFXTreeBuilder_sgmlop(object):
    def __init__(self, verbose=False):
        import sgmlop
        self.__builder = ET.TreeBuilder()
        self.__parser = sgmlop.SGMLParser()
        self.__parser.register(self)
        self.inside_data = False
        self.latest_starttag = None
        self.verbose = verbose

    def feed(self, data):
        self.__parser.feed(data)

    def close(self):
        self.__parser.close()
        self.__parser = None
        return self.__builder.close()

    def finish_starttag(self, tag, attrib):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "starttag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if self.verbose:
            msg = "starttag opening '%s'" % tag
            print msg
        self.__builder.start(tag, attrib)
        self.latest_starttag = tag

    def finish_endtag(self, tag):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "endtag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if tag != self.latest_starttag:
            if self.verbose:
                msg = "endtag closing '%s'" % tag
                print msg
            self.__builder.end(tag)

    def handle_data(self, text):
        text = text.strip('\f\n\r\t\v') # Strip whitespace, except space char
        if text:
            if self.verbose:
                msg = "handle_data adding data '%s'" % text
                print msg
            self.inside_data = True
            self.__builder.data(text)


class ReportBase(object):
    def __init__(self, **kwargs):
        for key,value in kwargs.iteritems():
            if value:
                setattr(self, key, value)

    def __repr__(self):
        return unicode(self)

class Transaction(ReportBase):
    def __unicode__(self):
        id = "FIXME"
        return '<%s %s>' % (self.__class__.__name__, id)

class Security(ReportBase):
    def __unicode__(self):
        id = self.ticker or '%s %s' % (self.uniqueidtype, self.uniqueid)
        return '<%s %s>' % (self.__class__.__name__, id)

class InvTransaction(ReportBase):
    def __unicode__(self):
        id = self.fitid
        return '<%s %s>' % (self.__class__.__name__, id)

class Position(ReportBase):
        def __unicode__(self):
            id = self.security
            return '<%s %s>' % (self.__class__.__name__, id)

class InvBalance(ReportBase):
        def __unicode__(self):
            id = ''
            return '<%s %s>' % (self.__class__.__name__, id)

def main():
    from optparse import OptionParser
    optparser = OptionParser(usage='usage: %prog FILE')
    optparser.set_defaults(verbose=False)
    optparser.add_option('-v', '--verbose', action='store_true',
                        help='Turn on parser debug output')
    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.error('incorrect number of arguments')
    FILE = args[0]
    ofxparser = OFXParser(verbose=options.verbose)
    ofxparser.parse(FILE)

if __name__ == '__main__':
    main()