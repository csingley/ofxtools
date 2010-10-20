#!/usr/bin/env python
import sys
import os
import xml.etree.cElementTree as ET
from decimal import Decimal

try:
    import elixir
    HAS_ELIXIR = True
except ImportError:
    HAS_ELIXIR = False
else:
    import db

from utilities import OFXv1, OFXv2

HEADER_FIELDS = {'100': ('DATA', 'VERSION', 'SECURITY', 'ENCODING', 'CHARSET',
                        'COMPRESSION', 'OLDFILEUID', 'NEWFILEUID'),}

class OFXParser(object):
    """
    Reads OFX files (v1 & v2), converts to ElementTree, and extracts the
    interesting data to a SQL database.
    """
    def __init__(self, verbose=False, url=None):
        self.reset()
        self.verbose = verbose
        self.url = url

    def reset(self):
        self.header = None
        self.tree = ET.ElementTree()
        self.connection = None

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source, 'rb')
        self.header, source = self.unwrap(source)
        root = self._parse(source)
        assert root.tag == 'OFX'

        if HAS_ELIXIR:
            self.translate()

    def unwrap(self, source):
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
                    for f in HEADER_FIELDS[header_version]])
            header[header_key] = header_version
            # Sanity check
            assert header['DATA'] == 'OFXSGML'
            assert header['VERSION'] in OFXv1
            #if header['VERSION'] not in valid.OFXv1:
                #print "OFXv1 header claims OFX version is %s" % header['VERSION']
        elif line1.startswith('<?xml'):
            #OFXv2
            # OFX declaration is the next line of content
            ofx_decl = next_nonempty_line(source)
            assert ofx_decl.endswith('?>')
            args = ofx_decl[:-3].split(' ')[1:]
            header = dict([arg.split('=') for arg in args])
            # Sanity check
            assert header['VERSION'] in OFXv2
        else:
            raise ValueError("Malformed OFX header '%s'" % line1)

        return header, source

    def _parse(self, source):
        # Mark the beginning of the tag soup.
        # This is generally not going to be seek(0), because we've
        # already stepped through the OFX header in unwrapOFX().
        beginning = source.tell()
        try:
            # If sgmlop is installed, it's the fastest parser
            # and it will handle OFXv1-style unclosed tags.
            parser = OFXTreeBuilder_sgmlop(verbose=self.verbose)
        except ImportError:
            # expat (Python's bundled XML parser) is compiled C: fast.
            # expat doesn't validate against DTDs; it will work as long
            # as all tags are closed explicitly, which is allowed by
            # OFXv1 and actually done by some FIs.
            parser = ET.XMLParser()
            try:
                root = self.tree.parse(source, parser)
            except SyntaxError:
                # Fall back to SGMLParser (slow, but handles unclosed tags)
                parser = OFXTreeBuilder(verbose=self.verbose)
                # expat already started reading the file; rewind
                source.seek(beginning)
                root = self.tree.parse(source, parser)
        else:
            root = self.tree.parse(source, parser)
        return root

    def translate(self):
        engine = elixir.sqlalchemy.create_engine(self.url or 'sqlite://',
                                                echo=self.verbose)
        self.connection = engine.connect()
        elixir.metadata.bind = self.connection
        elixir.setup_all()
        elixir.create_all()

        try:
            sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
            self.handleSTATUS(sonrs.find('STATUS'))

            stmttrnrs = self.tree.find('BANKMSGSRSV1/STMTTRNRS')
            if stmttrnrs:
                trnuid = stmttrnrs.find('TRNUID').text
                self.handleSTATUS(stmttrnrs.find('STATUS'))
                stmtrss = stmttrnrs.findall('STMTRS')
                for stmtrs in stmtrss:
                    self.handleSTMTRS(stmtrs, trnuid)

            ccstmttrnrs = self.tree.find('CREDITCARDMSGSRSV1/CCSTMTTRNRS')
            if ccstmttrnrs:
                trnuid = ccstmttrnrs.find('TRNUID').text
                self.handleSTATUS(ccstmttrnrs.find('STATUS'))
                stmtrss = ccstmttrnrs.findall('STMTRS')
                for ccstmtrs in stmtrss:
                    self.handleSTMTRS(ccstmtrs, trnuid)

            seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')

            invstmttrnrs = self.tree.find('INVSTMTMSGSRSV1/INVSTMTTRNRS')
            if invstmttrnrs:
                trnuid = invstmttrnrs.find('TRNUID').text
                self.handleSTATUS(invstmttrnrs.find('STATUS'))
                invstmtrss = invstmttrnrs.findall('INVSTMTRS')
                for invstmtrs in invstmtrss:
                    self.handleINVSTMTRS(invstmtrs, seclist, trnuid)
        except:
            elixir.session.rollback()
            raise
        else:
            elixir.session.commit()

    def flatten(self, element):
        """
        Recurse through aggregate and flatten into an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
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
                # Silently drop all private tags (e.g. <INTU.XXXX>
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # element is an aggregate.
                assert tag not in aggregates
                aggregates.update(self.flatten(child))
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggregates.keys():
            assert key not in leaves
        leaves.update(aggregates)
        return leaves

    def handleSTATUS(self, status):
        attrs = self.flatten(status)
        severity = attrs['severity']
        assert severity in ('INFO', 'WARN', 'ERROR')
        if severity == 'ERROR':
            # FIXME - handle errors
            pass
        elif severity == 'WARN':
            # FIXME - handle errors
            pass

    def handleSTMTRS(self, stmtrs, trnuid):
        acct_attrs = {'curdef': stmtrs.find('CURDEF').text,}
        acct_attrs.update(self.flatten(stmtrs.find('BANKACCTFROM')))
        acct = db.BANKACCT(**acct_attrs)

        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            log = db.TRANLOG(trnuid=trnuid, dtstart=dtstart.text, dtend=dtend.text)
            for tran in tranlist:
                attrs = self.flatten(tran)
                # Add FKs for ACCT, TRANLOG
                attrs['acct'] = acct
                attrs['log'] = log
                db.STMTTRN(**attrs)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        attrs = self.flatten(ledgerbal)
        attrs['ledgerbal'] = attrs.pop('balamt')
        attrs['acct'] = acct
        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal:
            # FIXME - check that AVAILBAL.DTASOF matches LEDGERBAL.DTASOF
            attrs['availbal'] = availbal.find('BALAMT').text
        db.BANKBAL(**attrs)

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            for fibal in ballist:
                attrs = self.flatten(fibal)
                attrs['acct'] = acct
                db.FIBAL(**attrs)

    def handleINVSTMTRS(self, stmtrs, seclist, trnuid):
        # Create Securities instances, and store in a map of
        #  (uniqueidtype, uniqueid) -> Security for quick lookup
        if seclist is not None:
            def handle_sec(element):
                instance = self.handleSEC(element)
                return ((instance.uniqueidtype, instance.uniqueid), instance)
            self.secs = dict([handle_sec(sec) for sec in seclist])

        self.dtasof = stmtrs.find('DTASOF').text
        acct_attrs = {'curdef': stmtrs.find('CURDEF').text,}
        acct_attrs.update(self.flatten(stmtrs.find('INVACCTFROM')))
        acct = db.INVACCT(**acct_attrs)

        # INVTRANLIST
        tranlist = stmtrs.find('INVTRANLIST')
        if tranlist:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            log = db.TRANLOG(trnuid=trnuid, dtstart=dtstart.text, dtend=dtend.text)
            invbanktrans = tranlist.findall('INVBANKTRAN')
            for invbanktran in invbanktrans:
                tranlist.remove(invbanktran)
                attrs = self.flatten(invbanktran)
                attrs['acct'] = acct
                attrs['log'] = log
                db.INVBANKTRAN(**attrs)
            for trn in tranlist:
                secClass = getattr(db, trn.tag)
                attrs = self.flatten(trn)
                #if 'uniqueid' in attrs:
                if issubclass(secClass, (db.INVBUY, db.INVSELL, db.CLOSUREOPT,
                                        db.INCOME, db.INVEXPENSE, db.JRNLSEC,
                                        db.REINVEST, db.RETOFCAP, db.SPLIT,
                                        db.TRANSFER)):
                    attrs['sec'] = self.secs[(attrs.pop('uniqueidtype'),
                                                attrs.pop('uniqueid'))]
                attrs['acct'] = acct
                attrs['log'] = log
                secClass(**attrs)

        # INVPOSLIST
        poslist = stmtrs.find('INVPOSLIST')
        if poslist:
            for pos in poslist:
                secClass = getattr(db, pos.tag)
                attrs = self.flatten(pos)
                attrs['acct'] = acct
                sec = attrs['sec'] = self.secs[(attrs.pop('uniqueidtype'), attrs.pop('uniqueid'))]

                # Strip out pricing data from the positions
                price_attrs = {'sec': sec}
                price_attrs.update(dict([(a, attrs.pop(a, None))
                    for a in ('dtpriceasof', 'unitprice', 'cursym', 'currate')]))
                price_attrs['cursym'] = price_attrs['cursym'] or acct.curdef

                db.SECPRICE(**price_attrs)

                secClass(**attrs)

        # INVBAL
        invbal = stmtrs.find('INVBAL')
        if invbal:
            # Strip off BALLIST
            ballist = invbal.find('BALLIST')
            if ballist:
                invbal.remove(ballist)
                for fibal in ballist:
                    attrs = self.flatten(fibal)
                    attrs['acct'] = acct
                    db.FIBAL(**attrs)
            attrs = self.flatten(invbal)
            attrs['acct'] = acct
            attrs['dtasof'] = self.dtasof
            db.INVBAL(**attrs)

        # INVOOLIST - not supported
        invoolist = stmtrs.find('INVOOLIST')
        if invoolist:
            stmtrs.remove(invoolist)

        # INV401K - not supported
        inv401k = stmtrs.find('INV401K')
        if inv401k:
            stmtrs.remove(inv401k)

        # INV401KBAL - not supported
        inv401kbal = stmtrs.find('INV401KBAL')
        if inv401kbal:
            stmtrs.remove(inv401kbal)

        # MKTGINFO - not supported
        mktginfo = stmtrs.find('MKTGINFO')
        if mktginfo:
            stmtrs.remove(mktginfo)

    def handleSEC(self, element):
        # Strip MFASSETCLASS/FIMFASSETCLASS - lists that will blow up flatten()
        mfassetclass = element.find('MFASSETCLASS')
        if mfassetclass:
            element.remove(mfassetclass)
        fimfassetclass = element.find('FIMFASSETCLASS')
        if fimfassetclass:
            element.remove(fimfassetclass)
        secClass = getattr(db, element.tag)
        attrs = self.flatten(element)
        instance = secClass(**attrs)
        if mfassetclass:
            for portion in mfassetclass:
                attrs = self.flatten(portion)
                attrs['mf'] = instance
                db.MFASSETCLASS(**attrs)
        if fimfassetclass:
            for portion in fimfassetclass:
                attrs = self.flatten(portion)
                attrs['mf'] = instance
                db.FIMFASSETCLASS(**attrs)
        return instance


from sgmllib import SGMLParser
class OFXTreeBuilder(SGMLParser):
    """
    Parses OFX v1&v2 into an ElementTree instance.
    Accessible via standard feed/close consumer interface.

    Built on sgmllib, which is deprecated and going away in py3k.
    """
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
        #text = text.strip('\f\n\r\t\v') # Strip whitespace, except space char
        text = text.strip()
        if text:
            if self.verbose:
                msg = "handle_data adding data '%s'" % text
                print msg
            self.inside_data = True
            self.__builder.data(text)

class OFXTreeBuilder_sgmlop(object):
    """
    Parses OFX v1&v2 into an ElementTree instance.
    Accessible via standard feed/close consumer interface.

    Built on sgmlop, which is deprecated and going away in py3k:
        http://bugs.python.org/issue1772916
    Nevertheless sgmlop is the best parser available, and can be gotten here:
        http://effbot.org/zone/sgmlop-index.htm
    """
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
        # "Note that if you use the standard pattern where a parser class holds
        #  a reference to the sgmlop object, and you'll register methods in the
        #  same class, Python may leak resources. To avoid this, you can either
        #  remove the object from the class before you destroy the class instance,
        #  or unregister all methods (by calling register(None)), or both.
        #  Recent versions of sgmlop supports proper garbage collection for
        #  this situation, but it never hurts to be on the safe side."
        # http://effbot.org/zone/sgmlop-handbook.htm
        self.__parser.register(None)
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
        #text = text.strip('\f\n\r\t\v') # Strip whitespace, except space char
        text = text.strip()
        if text:
            if self.verbose:
                msg = "handle_data adding data '%s'" % text
                print msg
            self.inside_data = True
            self.__builder.data(text)


def main():
    from optparse import OptionParser
    optparser = OptionParser(usage='usage: %prog FILE')
    optparser.set_defaults(verbose=False, database=None)
    optparser.add_option('-v', '--verbose', action='store_true',
                        help='Turn on debug output')
    optparser.add_option('-d', '--database',
                        help='URL of persistent database')
    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.print_usage()
        sys.exit(-1)
    FILE = args[0]

    ofxparser = OFXParser(verbose=options.verbose,
                        url=options.database)
    ofxparser.parse(FILE)

if __name__ == '__main__':
    main()
