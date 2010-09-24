#!/usr/bin/env python2
import os
import xml.etree.cElementTree as ET

import valid

### ELEMENT HANDLER CLASSES
# After the OFX data have been parsed into an ElementTree structure,
# the interesting parts of the tree get passed into these classes for
# further processing.  The handlers validate the data, convert them
# from strings into Python data structurs, and flatten them into
# un-nested dictionaries and lists of dictionaries.
#
# Having accomplished that, these handler classes simply store the data as
# object attributes to be accessed.  You can subclass these handlers and
# override the top-level handling methods in order to perform more extensive
# processing.  In particular, the data model here is intended to facilitate
# persistence into a relational database.
class ReportBase(object):
    def __init__(self, **attrs):
        for key,value in attrs.iteritems():
            if value is not None:
                setattr(self, key, value)

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        id = "FIXME"
        return '<%s %s>' % (self.__class__.__name__, id)


class Account(ReportBase):
    pass


class BankAccount(Account):
    pass


class CcAccount(Account):
    pass


class InvAccount(Account):
    pass


class Transaction(ReportBase):
    pass


class Security(ReportBase):
    def __unicode__(self):
        id = self.ticker or '%s %s' % (self.uniqueidtype, self.uniqueid)
        return '<%s %s>' % (self.__class__.__name__, id)


class InvTransaction(ReportBase):
    def __unicode__(self):
        id = self.fitid
        return '<%s %s>' % (self.__class__.__name__, id)


class Position(ReportBase):
    def __init__(self, **attrs):
        price_attrs = {'secid': attrs['secid'],}
        for attr in ('unitprice','dtpriceasof'):
            price_attrs[attr] = attrs.pop(attr)
        self.price = Price(**price_attrs)

        super(Position, self).__init__(**attrs)

    def __unicode__(self):
        id = self.secid
        return '<%s %s>' % (self.__class__.__name__, id)

class Price(ReportBase):
    def __unicode__(self):
        id = "FIXME"
        return '<%s %s>' % (self.__class__.__name__, id)


class Response(ReportBase):
    def handle_element(self, element, recurse=True):
        """
        General-purpose element handler.  Uses the element tag to look up the
        right validator & convert element data text into Python data types.
        Recurses through aggregates and flattens them into un-nested dicts.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from the element before passing it in here.

        The switch to turn off recursion (i.e. only handle top-level elements
        in an aggregate & ignore subaggregates) is a convenience for getting
        at DTSTART and DTEND in TRANSLIST aggregates.
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
            elif recurse:
                # element is an aggregate and we haven't turned off recursion.
                # dispatch parse method; fallback to default (recurse here).
                handlerMethod = getattr(self, 'handle_%s' % tag, self.handle_element)
                assert tag not in aggregates
                aggregates.update(handlerMethod(child))
        # Validate leaves; aggregates are already validated by parse method.
        validation_schema = getattr(valid, element.tag)
        results = validation_schema.to_python(leaves)
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggregates.keys():
            assert key not in leaves.keys()
        results.update(aggregates)
        return results


class Signon(Response):
    code = None
    severity = None
    message = None
    dtserver = None
    userkey = None
    tskeyexpire = None
    language = None
    dtprofup = None
    dtacctup = None
    org = None
    fid = None
    sesscookie = None
    accesskey = None

    def __init__(self, sonrs):
        self.handle_sonrs(sonrs)

    def handle_sonrs(self, sonrs):
        attr = self.handle_element(sonrs)
        for key, value in attr.iteritems():
            if value is not None:
                setattr(self, key, value)


class Statement(Response):
    account = None
    default_currency = None
    transactions = []
    start = None
    end = None
    asof = None
    other_balances = {}
    code = None
    code = None

    def handle_stmttrnrs(self, stmttrnrs):
        status = self.handle_element(stmttrnrs.find('STATUS'))
        self.code = status['code']
        self.severity = status['severity']
        self.message = status['message']

    def handle_stmtrs(self, stmtrs):
        # Override in subclass
        raise ValueError

    def handle_list_item(self, item, validator, object_class,
        extra_attributes=None):
        # Convert the body of the item
        attr = self.handle_element(item)

        # Merge in the item type from the tag
        assert 'type' not in attr.keys()
        attr['type'] = validator.to_python(item.tag)

        # Check for namespace collisions, then merge in any extra
        # attributes passed in.
        extra_attributes = extra_attributes or {}
        attr_keys = attr.keys()
        for key in extra_attributes.keys():
            assert key not in attr_keys
        attr.update(extra_attributes)

        return object_class(**attr)

    def handle_tranlist(self, tranlist):
        tranlist_preamble = self.handle_element(tranlist, recurse=False)
        self.transactions = [self.handle_list_item(tran,
                        self.transaction_validator, self.TransactionClass) \
                        for tran in tranlist[2:]]
        self.start = tranlist_preamble['dtstart']
        self.end = tranlist_preamble['dtend']

    def handle_ballist(self, ballist):
        def handle_bal(bal):
            bal = self.handle_element(bal)
            return bal.pop('name'), bal
        return dict([handle_bal(bal) for bal in ballist])


class BankStatement(Statement):
    ledger_balance = None
    available_balance = None

    AccountClass = BankAccount
    TransactionClass = Transaction

    transaction_validator = valid.BANKTRANLISTitem

    #def __init__(self, stmtrs):
        #self.handle_stmtrs(stmtrs)

    def __init__(self, stmttrnrs):
        self.handle_stmttrnrs(stmttrnrs)
        stmtrs = stmttrnrs.find('STMTRS')
        if stmtrs:
            self.handle_stmtrs(stmtrs)

    def handle_stmtrs(self, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist:
            self.handle_tranlist(tranlist)
            stmtrs.remove(tranlist)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        self.handle_ledgerbal(ledgerbal)
        stmtrs.remove(ledgerbal)

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal:
            self.handle_availbal(availbal)
            stmtrs.remove(availbal)

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.other_balances = self.handle_ballist(ballist)
            stmtrs.remove(ballist)

        # MKTGINFO - not supported
        mktginfo = stmtrs.find('MKTGINFO')
        if mktginfo:
            stmtrs.remove(mktginfo)

        dregs = self.handle_element(stmtrs)
        self.curdef = dregs.pop('curdef')
        self.account = self.AccountClass(**dregs)

    def handle_ledgerbal(self, ledgerbal):
        ledgerbal = self.handle_element(ledgerbal)
        self.ledger_balance = (ledgerbal['dtasof'], ledgerbal['balamt'])

    def handle_availbal(self, availbal):
        availbal = self.handle_element(availbal)
        self.available_balance = (availbal['dtasof'], availbal['balamt'])


class CreditCardStatement(BankStatement):
    AccountClass = CcAccount

    def __init__(self, stmttrnrs):
        self.handle_stmttrnrs(stmttrnrs)
        stmtrs = stmttrnrs.find('CCSTMTRS')
        self.handle_stmtrs(stmtrs)

class InvestmentStatement(Statement):
    positions = []
    available_cash = None
    margin_balance = None
    short_balance = None
    buying_power = None

    AccountClass = InvAccount
    SecurityClass = Security
    TransactionClass = InvTransaction
    PositionClass = Position

    transaction_validator = valid.INVTRANLISTitem

    #def __init__(self, seclist, stmtrs):
        #self.handle_stmtrs(seclist, stmtrs)

    def __init__(self, seclist, stmttrnrs):
        self.handle_stmttrnrs(stmttrnrs)
        stmtrs = stmttrnrs.find('INVSTMTRS')
        if stmtrs:
            self.handle_stmtrs(seclist, stmtrs)

    def handle_stmtrs(self, seclist, stmtrs):
        # First create Securities instances, and store in a map of
        #  (uniqueidtype, uniqueid) -> Security for easy lookup
        self.securities = self.handle_SECLIST(seclist)

        # INVTRANLIST
        tranlist = stmtrs.find('INVTRANLIST')
        if tranlist:
            self.handle_tranlist(tranlist)
            stmtrs.remove(tranlist)

        # INVPOSLIST
        poslist = stmtrs.find('INVPOSLIST')
        if poslist:
            self.handle_poslist(poslist)
            stmtrs.remove(poslist)

        # INVBAL
        invbal = stmtrs.find('INVBAL')
        if invbal:
            self.handle_invbal(invbal)
            # Once BALLIST is stripped out, we don't need to remove INVBAL,
            # which contains no other subaggregates.  It'll get processed
            # along with the dregs.

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

        dregs = self.handle_element(stmtrs)

        # Instantiate INVACCTFROM
        acct_attrs = {'brokerid': dregs.pop('brokerid'),}
        acct_attrs['acctid'] = dregs.pop('acctid')
        self.account = self.AccountClass(**acct_attrs)

        for key, value in dregs.iteritems():
            setattr(self, key, value)

    def handle_SECLIST(self, seclist):
        def handle_sec(element):
            # Strip out SECID so self.handle_element() won't dispatch it to
            # self.handle_SECID(), which method we actually use to perform
            # the lookups we're constructing here.
            secinfo = element.find('SECINFO')
            secid = secinfo.find('SECID')
            secinfo.remove(secid)

            # Flatten SECID and validate it manually
            secid_attr = dict([(child.tag.lower(), child.text) for child in secid])
            secid_attr = valid.SECID.to_python(secid_attr)

            # ...then parse the rest of the xxxINFO naively
            security = self.handle_list_item(element, valid.SECLISTitem,
                    self.SecurityClass, extra_attributes=secid_attr)
            return (security.uniqueidtype, security.uniqueid), security
        if seclist is not None:
            return dict([handle_sec(sec) for sec in seclist])

    def handle_SECID(self, element):
        # Validate
        results = self.handle_element(element)
        # Transform to Security instance
        sec = self.securities[(results['uniqueidtype'], results['uniqueid'])]
        return {'secid': sec}

    def handle_poslist(self, poslist):
        positions = [self.handle_list_item(pos, valid.POSLISTitem, \
                        self.PositionClass) for pos in poslist]
        # Strip out pricing data from the positions
        def strip_price(pos):
            price = pos.price
            del pos.price
            return price

        self.positions = positions
        self.prices = [strip_price(pos) for pos in positions]

    def handle_invbal(self, invbal):
        # Strip off BALLIST and parse it
        ballist = invbal.find('BALLIST')
        if ballist:
            self.other_balances = self.handle_ballist(ballist)
            invbal.remove(ballist)

### PARSER CLASSES
# These classes convert OFX data into a Python ElementTree structure.

class OFXParser(object):
    """
    Reads OFX files (v1 & v2) and extracts the interesting data.
    """
    SignonHandler = Signon
    BankHandler = BankStatement
    CcHandler = CreditCardStatement
    InvHandler = InvestmentStatement

    def __init__(self, verbose=False):
        self.reset()
        self.verbose = verbose

    def reset(self):
        self.header = None
        self.tree = ET.ElementTree()
        self.signon = None
        self.bank_statement = None
        self.creditcard_statement = None
        self.investment_statement = None

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source, 'rb')
        self.header, source = self.unwrapOFX(source)
        root = self._parse(source)
        assert root.tag == 'OFX'

        sonrs = root.find('SIGNONMSGSRSV1/SONRS')
        self.signon = signon = self.SignonHandler(sonrs)

        stmttrnrs = root.find('BANKMSGSRSV1/STMTTRNRS')
        if stmttrnrs:
            self.bank_statement = self.BankHandler(stmttrnrs)

        ccstmttrnrs = root.find('CREDITCARDMSGSRSV1/CCSTMTTRNRS')
        if ccstmttrnrs:
            self.creditcard_statement = self.CcHandler(ccstmttrnrs)

        seclist = root.find('SECLISTMSGSRSV1/SECLIST')
        invstmttrnrs = root.find('INVSTMTMSGSRSV1/INVSTMTTRNRS')
        if invstmttrnrs:
            self.investment_statement = self.InvHandler(seclist, invstmttrnrs)

        errors = {}
        if signon.code:
            errors.update({'signon':{'code': signon.code, 'severity': signon.severity, 'message': signon.message}})

        for msg in ('bank', 'creditcard', 'investment'):
            stmt = getattr(self, '%s_statement' % msg)
            if stmt and stmt.code:
                d = dict([(tag, getattr(stmt, tag)) \
                            for tag in ('code', 'severity', 'message')])
                errors.update({msg: d})

        return errors

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
    ofxparser = OFXParser(verbose=options.verbose)
    errors = ofxparser.parse(FILE)
    print errors

if __name__ == '__main__':
    main()
