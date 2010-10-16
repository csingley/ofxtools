#!/usr/bin/env python
import os
import xml.etree.cElementTree as ET
from decimal import Decimal

import valid
import db

#"""
#Quicken will attempt to match securities downloaded in the SECLIST to
#securities in Quicken using the following logic.

#First, Quicken checks to see if the security has already been matched
#by comparing the CUSIP or UNIQUEID in the download to the unique
#identifier stored in the Quicken database. If there is a match, then
#no additional steps are taken.

#When Quicken does not find a match based on CUSIP, it will compare the
#downloaded security name to the security names in the file. It will match
#the security, if it finds an exact match for the security name.

#Next, Quicken compares the ticker downloaded to the symbol for each
#security. When a ticker in the download matches the symbol for a security
#in the Quicken database, Quicken matches them. When there is no symbol for
#the security on the security list, Quicken skips this step. Quicken will
#proceed to show the security matching dialog.

#When Quicken cannot find a match based on one of the three criteria above,
#it will show the security matching dialog.
#"""
#http://fi.intuit.com/ofximplementation/dl/OFXDataMappingGuide.pdf


class OFXParser(object):
    """
    Reads OFX files (v1 & v2), converts to ElementTree, and extracts the
    interesting data to a SQL database.
    """
    def __init__(self, verbose=False):
        self.reset()
        self.verbose = verbose

    def reset(self):
        self.header = None
        self.tree = ET.ElementTree()

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source, 'rb')
        self.header, source = self.unwrapOFX(source)
        root = self._parse(source)
        assert root.tag == 'OFX'

        sonrs = root.find('SIGNONMSGSRSV1/SONRS')
        # FIXME - handle errors
        self.flatten(sonrs)

        stmttrnrs = root.find('BANKMSGSRSV1/STMTTRNRS')
        if stmttrnrs:
            # FIXME - handle errors
            self.flatten(stmttrnrs)
            stmtrs = stmttrnrs.find('STMTRS')
            self.handleSTMTRS(stmtrs)

        ccstmttrnrs = root.find('CREDITCARDMSGSRSV1/CCSTMTTRNRS')
        if ccstmttrnrs:
            # FIXME - handle errors
            self.flatten(ccstmttrnrs)
            stmtrs = stmttrnrs.find('STMTRS')
            self.handleSTMTRS(ccstmtrs)

        seclist = root.find('SECLISTMSGSRSV1/SECLIST')
        invstmttrnrs = root.find('INVSTMTMSGSRSV1/INVSTMTTRNRS')
        if invstmttrnrs:
            # FIXME - handle errors
            self.flatten(invstmttrnrs)
            invstmtrs = invstmttrnrs.find('INVSTMTRS')
            self.handleINVSTMTRS(invstmtrs, seclist)

        #errors = {}
        #if signon.code:
            #errors.update({'signon':{'code': signon.code, 'severity': signon.severity, 'message': signon.message}})

        #for msg in ('bank', 'creditcard', 'investment'):
            #stmt = getattr(self, '%s_statement' % msg)
            #if stmt and stmt.code:
                #d = dict([(tag, getattr(stmt, tag)) \
                            #for tag in ('code', 'severity', 'message')])
                #errors.update({msg: d})

        #return errors

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
            assert header['VERSION'] in valid.OFXv2
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

    def handleSTMTRS(self, stmtrs):
        acct_attrs = {'curdef': stmtrs.find('CURDEF').text,}
        acct_attrs.update(self.flatten(stmtrs.find('BANKACCTFROM')))
        self.acct = db.BANKACCT(**acct_attrs)

        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist:
            self.dtstart, self.dtend = dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            for tran in tranlist:
                attrs = self.flatten(tran)
                # Add FK for Account
                attrs['acct'] = self.acct
                db.STMTTRN(**attrs)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        attrs = self.flatten(ledgerbal)
        attrs['ledgerbal'] = attrs.pop('balamt')
        attrs['acct'] = self.acct
        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal:
            attrs['availbal'] = availbal.find('BALAMT').text
        db.BANKBAL(**attrs)

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            for fibal in ballist:
                attrs = self.flatten(fibal)
                attrs['acct'] = self.acct
                db.FIBAL(**attrs)

    def handleINVSTMTRS(self, stmtrs, seclist):
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
        self.acct = db.INVACCT(**acct_attrs)

        # INVTRANLIST
        tranlist = stmtrs.find('INVTRANLIST')
        if tranlist:
            self.dtstart, self.dtend = dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            invbanktrans = tranlist.findall('INVBANKTRAN')
            for invbanktran in invbanktrans:
                tranlist.remove(invbanktran)
                stmttrn = invbanktran[0]
                attrs = self.flatten(stmttrn)
                attrs['acct'] = self.acct
                db.STMTTRN(**attrs)
            for trn in tranlist:
                secClass = getattr(db, trn.tag)
                attrs = self.flatten(trn)
                if 'uniqueid' in attrs:
                    attrs['sec'] = self.secs[(attrs.pop('uniqueidtype'), attrs.pop('uniqueid'))]
                attrs['acct'] = self.acct
                secClass(**attrs)

        # INVPOSLIST
        poslist = stmtrs.find('INVPOSLIST')
        if poslist:
            for pos in poslist:
                secClass = getattr(db, pos.tag)
                attrs = self.flatten(pos)
                attrs['acct'] = self.acct
                sec = attrs['sec'] = self.secs[(attrs.pop('uniqueidtype'), attrs.pop('uniqueid'))]

                # Strip out pricing data from the positions
                price_attrs = {'sec': sec}
                price_attrs.update(dict([(a, attrs.pop(a, None))
                    for a in ('dtpriceasof', 'unitprice', 'cursym', 'currate')]))
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
                    attrs['acct'] = self.acct
                    db.FIBAL(**attrs)
            attrs = self.flatten(invbal)
            attrs['acct'] = self.acct
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
        text = text.strip
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
    optparser.set_defaults(verbose=False,)
    optparser.add_option('-v', '--verbose', action='store_true',
                        help='Turn on parser debug output')
    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.print_usage()
    FILE = args[0]

    import elixir
    elixir.metadata.bind = "sqlite:///test.sqlite"
    elixir.setup_all()
    elixir.create_all()

    ofxparser = OFXParser(verbose=options.verbose)
    errors = ofxparser.parse(FILE)

    elixir.session.commit()

    print errors

if __name__ == '__main__':
    main()
