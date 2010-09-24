#!/usr/bin/env python2
import datetime
import uuid
from xml.etree.cElementTree import Element, SubElement, tostring
import urllib2
import os
import ConfigParser
from cStringIO import StringIO

import valid
from parser import OFXParser
from utilities import _, parse_accts, acct_re

dtConverter = valid.OFXDtConverter()
stringBool = valid.OFXStringBool()
accttypeValidator = valid.validators.OneOf(valid.ACCOUNT_TYPES)

class OFXClient(object):
    """ """
    appids = ('QWIN', # Quicken for Windows
                'QMOFX', # Quicken for Mac
                'QBW', # QuickBooks for Windows
                'QBM', # QuickBooks for Mac
                'Money', # MSFT Money
                'Money Plus', # MSFT Money Plus
    )
    appvers = ('1500', # Quicken 2006/ Money 2006
                '1600', # Quicken 2007/ Money 2007/ QuickBooks 2006
                '1700', # Quicken 2008/ Money Plus/ QuickBooks 2007
                '1800', # Quicken 2009/ QuickBooks 2008
                '1900', # Quicken 2010/ QuickBooks 2009
                '2000', # QuickBooks 2010
    )

    def __init__(self, url, **kwargs):
        self.url = url
        defaults = {'version': 102, 'appid': 'QWIN', 'appver': '1800'}
        for attr in ('org', 'fid', 'version', 'appid', 'appver'):
            setattr(self, attr, kwargs.get(attr, defaults.get(attr, None)))
        self.version = int(self.version)
        assert self.appid in self.appids
        assert self.appver in self.appvers

        # Initialize
        self.reset()

    def reset(self):
        self.signon = None
        self.bank = None
        self.creditcard = None
        self.investment = None
        self.request = None
        self.response = None

    @classmethod
    def from_config(cls, **kwargs):
        client = cls(**kwargs)
        client.encode(**kwargs)
        return client

    def encode(self, **kwargs):
        bank_opts = dict([(k, kwargs[k]) for k in ('inctran', 'dtstart', 'dtend')])
        inv_opts = dict([(k, kwargs[k]) for k in ('incpos', 'dtasof', 'incbal')])
        inv_opts.update(bank_opts)

        for accttype in ('bank', 'creditcard'):
            accts = kwargs.get('%s_accounts' % accttype, None)
            if accts:
                write_method = getattr(self, 'write_%s' % accttype)
                write_method(accts, **bank_opts)

        invaccts = kwargs.get('investment_accounts', None)
        if invaccts:
            self.write_investment(invaccts, **inv_opts)

    def download(self, user=None, password=None, parse=False, archive_dir=None):
        mime = 'application/x-ofx'
        headers = {'Content-type': mime, 'Accept': '*/*, %s' % mime}
        if not self.request:
            self.write_request(user, password)
        http = urllib2.Request(self.url, self.request, headers)
        try:
            self.response = response = urllib2.urlopen(http)
        except urllib2.HTTPError as err:
            # FIXME
            raise
        # urllib2.urlopen returns an addinfourl instance, which supports
        # a limited subset of file methods.  Copy response to a StringIO
        # so that we can use tell() and seek().
        source = StringIO()
        source.write(response.read())
        # After writing, rewind to the beginning.
        source.seek(0)

        ofxparser = OFXParser()
        errors = ofxparser.parse(source)
        # Rewind source again after parsing
        source.seek(0)

        # Check for errors
        if errors:
            # FIXME
            raise ValueError("OFX download errors: '%s'" % str(errors))

        if archive_dir:
            archive_path = os.path.join(archive_dir, '%s.ofx' % signon.dtserver.strftime('%Y%m%d%H%M%S'))
            with open(archive_path, 'w') as archive:
                archive.write(source.read())
            # Rewind source again after copying
            source.seek(0)

        if parse:
            return ofxparser
        else:
            return source

    def write_request(self, user=None, password=None):
        ofx = Element('OFX')
        if not self.signon:
            self.write_signon(user, password)
        ofx.append(self.signon)
        for msgset in ('bank', 'creditcard', 'investment'):
            msgset = getattr(self, msgset, None)
            if msgset:
                ofx.append(msgset)
        self.request = request = self.header + tostring(ofx)
        return request

    @property
    def header(self):
        """ OFX header; prepend to OFX markup. """
        version = (self.version/100)*100 # Int division drops remainder
        if version == 100:
            # Flat text header
            fields = (  ('OFXHEADER', str(version)),
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
        elif version == 200:
            # XML header
            xml_decl = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
            fields = (  ('OFXHEADER', str(version)),
                        ('VERSION', str(self.version)),
                        ('SECURITY', 'NONE'),
                        ('OLDFILEUID', 'NONE'),
                        ('NEWFILEUID', str(uuid.uuid4())),
            )
            attrs = ['='.join(attr, '"%s"' %val) for attr,val in fields]
            ofx_decl = '<?OFX %s?>' % ' '.join(attrs)
            return '\r\n'.join((xml_decl, ofx_decl))
        else:
            # FIXME
            raise ValueError

    def write_signon(self, user, password):
        if not (user and password):
            # FIXME
            raise ValueError
        msgsrq = Element('SIGNONMSGSRQV1')
        sonrq = SubElement(msgsrq, 'SONRQ')
        SubElement(sonrq, 'DTCLIENT').text = dtConverter.from_python(datetime.datetime.now())
        SubElement(sonrq, 'USERID').text = user
        SubElement(sonrq, 'USERPASS').text = password
        SubElement(sonrq, 'LANGUAGE').text = 'ENG'
        if self.org:
            fi = SubElement(sonrq, 'FI')
            SubElement(fi, 'ORG').text = self.org
            if self.fid:
                SubElement(fi, 'FID').text = self.fid
        SubElement(sonrq, 'APPID').text = self.appid
        SubElement(sonrq, 'APPVER').text = self.appver
        self.signon = msgsrq

    def write_bank(self, accounts, inctran=True, dtstart=None, dtend=None):
        """
        Requesting transactions without dtstart/dtend (which is the default)
        asks for all transactions on record.
        """
        if not accounts:
            # FIXME
            raise ValueError('No bank accounts requested')
        msgsrq = Element('BANKMSGSRQV1')
        for account in accounts:
            try:
                accttype, bankid, acctid = account
                accttype = accttypeValidator.to_python(accttype)
            except ValueError:
                # FIXME
                raise ValueError("Bank accounts must be specified as a sequence of (ACCTTYPE, BANKID, ACCTID) tuples, not '%s'" % str(accounts))
            stmtrq = self.wrap_request(msgsrq, 'STMTRQ')
            acctfrom = SubElement(stmtrq, 'BANKACCTFROM')
            SubElement(acctfrom, 'BANKID').text = bankid
            SubElement(acctfrom, 'ACCTID').text = acctid
            SubElement(acctfrom, 'ACCTTYPE').text = accttype

            self.include_transactions(stmtrq, inctran, dtstart, dtend)
        self.bank = msgsrq

    def write_creditcard(self, accounts, inctran=True, dtstart=None, dtend=None):
        """
        Requesting transactions without dtstart/dtend (which is the default)
        asks for all transactions on record.
        """
        if not accounts:
            # FIXME
            raise ValueError('No credit card accounts requested')
        msgsrq = Element('CREDITCARDMSGSRQV1')
        for account in accounts:
            stmtrq = self.wrap_request(msgsrq, 'CCSTMTRQ')
            acctfrom = SubElement(stmtrq, 'CCACCTFROM')
            SubElement(acctfrom, 'ACCTID').text = account

            self.include_transactions(stmtrq, inctran, dtstart, dtend)
        self.creditcard = msgsrq

    def write_investment(self, accounts,
                    inctran=True, dtstart=None, dtend=None,
                    incpos=True, dtasof=None,
                    incbal=True):
        """ """
        if not accounts:
            # FIXME
            raise ValueError('No investment accounts requested')
        msgsrq = Element('INVSTMTMSGSRQV1')
        for account in accounts:
            try:
                brokerid, acctid = account
            except ValueError:
                raise ValueError("Investment accounts must be specified as a sequence of (BROKERID, ACCTID) tuples, not '%s'" % str(accounts))
            stmtrq = self.wrap_request(msgsrq, 'INVSTMTRQ')
            acctfrom = SubElement(stmtrq, 'INVACCTFROM')
            SubElement(acctfrom, 'BROKERID').text = brokerid
            SubElement(acctfrom, 'ACCTID').text = acctid

            self.include_transactions(stmtrq, inctran, dtstart, dtend)

            SubElement(stmtrq, 'INCOO').text = 'N'

            incpos = SubElement(stmtrq, 'INCPOS')
            if dtasof:
                SubElement(incpos, 'DTASOF').text = dtConverter.from_python(dtasof)
            SubElement(incpos, 'INCLUDE').text = stringBool.from_python(incpos)

            SubElement(stmtrq, 'INCBAL').text = stringBool.from_python(incbal)
        self.investment = msgsrq

    # Utilities
    def wrap_request(self, parent, tag):
        """ """
        assert 'TRNRQ' not in tag
        assert tag[-2:] == 'RQ'
        trnrq = SubElement(parent, tag.replace('RQ', 'TRNRQ'))
        SubElement(trnrq, 'TRNUID').text = str(uuid.uuid4())
        return SubElement(trnrq, tag)

    def include_transactions(self, parent, include=True, dtstart=None, dtend=None):
        inctran = SubElement(parent, 'INCTRAN')
        if dtstart:
            SubElement(inctran, 'DTSTART').text = dtConverter.from_python(dtstart)
        if dtend:
            SubElement(inctran, 'DTEND').text = dtConverter.from_python(dtend)
        SubElement(inctran, 'INCLUDE').text = stringBool.from_python(include)
        return inctran

def init_optionparser():
    from optparse import OptionParser, OptionGroup

    usage = "usage: %prog [options] institution"
    optparser = OptionParser(usage=usage)
    optparser.set_defaults(list=False, dry_run=False, config=None, user= None,
                            checking=None, savings=None, moneymrkt=None,
                            creditline=None, creditcard=None, investment=None,
                            inctran=True, dtstart=None, dtend=None,
                            incpos=True, dtasof=None, incbal=True)
    optparser.add_option('-l', '--list', action='store_true',
                        help='list known institutions and exit')
    optparser.add_option('-n', '--dry-run', action='store_true',
                        help='display OFX request and exit')
    optparser.add_option('-o', '--config', metavar='FILE', help='use alternate config file')
    optparser.add_option('-u', '--user', help='login user ID at institution')
    # Bank accounts
    bankgroup = OptionGroup(optparser, 'Bank accounts are specified as pairs of (routing#, acct#)')
    bankgroup.add_option('-c', '--checking', metavar='(LIST OF ACCOUNTS)')
    bankgroup.add_option('-a', '--savings', metavar='(LIST OF ACCOUNTS)')
    bankgroup.add_option('-m', '--moneymrkt', metavar='(LIST OF ACCOUNTS)')
    bankgroup.add_option('-r', '--creditline', metavar='(LIST OF ACCOUNTS)')
    optparser.add_option_group(bankgroup)

    # Credit card accounts
    ccgroup = OptionGroup(optparser, 'Credit cards are specified by an acct#')
    ccgroup.add_option('-C', '--creditcard', metavar='(LIST OF ACCOUNTS)')
    optparser.add_option_group(ccgroup)

    # Investment accounts
    invgroup = OptionGroup(optparser, 'Investment accounts are specified as pairs of (brokerid, acct#)')
    invgroup.add_option('-i', '--investment', metavar='(LIST OF ACCOUNTS)')
    optparser.add_option_group(invgroup)

    # Transaction options
    transgroup = OptionGroup(optparser, 'Transaction Options')
    transgroup.add_option('-t', '--skip-transactions', dest='inctran',
                        action='store_false')
    transgroup.add_option('-s', '--start', dest='dtstart')
    transgroup.add_option('-e', '--end', dest='dtend')
    optparser.add_option_group(transgroup)
    # Position options
    posgroup = OptionGroup(optparser, '(Investment) Position Options')
    posgroup.add_option('-p', '--skip-positions', dest='incpos',
                        action='store_false')
    posgroup.add_option('-d', '--date', dest='dtasof')
    optparser.add_option_group(posgroup)
    # Balance options
    balgroup = OptionGroup(optparser, '(Investment) Balance Options')
    balgroup.add_option('-b', '--skip-balances', dest='incbal',
                        action='store_false')
    optparser.add_option_group(balgroup)

    return optparser


class OFXConfigParser(ConfigParser.SafeConfigParser):
    """ """
    import re
    main_config = os.path.join(os.path.dirname(__file__), 'main.cfg')
    defaults = {'version': '102', 'appid': 'QWIN', 'appver': '1800',
                'org': None, 'fid': None, 'user': None,
                'bankid': None, 'brokerid': None,
                'checking': '', 'savings': '', 'moneymrkt': '',
                'creditline': '', 'creditcard': '', 'investment': ''}

    acct_re = re.compile(r'([\w.\-/]{1,22})')
    #bankaccts_re = re.compile(r'\(([\w.\-/]{1,9}),\s*([\w.\-/]{1,22})\)')
    pair_re = re.compile(r'\(([\w.\-/]{1,22}),\s*([\w.\-/]{1,22})\)')
    naked_re = re.compile(r'(\b)([\w.\-/]{1,22})')

    def __init__(self, defaults=None, dict_type=dict):
        defaults = defaults or self.defaults
        ConfigParser.SafeConfigParser.__init__(self, defaults, dict_type)

    def read(self, filenames=None):
        # First load main config
        self.readfp(open(self.main_config))
        # Then load user configs (defaults to main.cfg [global] config: value)
        filenames = filenames or _(self.get('global', 'config'))
        self.read_ok = ConfigParser.SafeConfigParser.read(self, filenames)
        # Finally, parse [global] and store for use by other methods
        self.process_global()
        return self.read_ok

    def process_global(self):
        # FIXME - extend beyond dir
        self.dir = _(self.get('global', 'dir'))

    @property
    def fi_index(self):
        sections = self.sections()
        sections.remove('global')
        return sections

    def setup_fi(self, fi, **kwargs):
        self.fi = fi

        # Options that are only specified via config
        for option in ('url', 'org', 'fid', 'bankid', 'brokerid',
                        'version', 'appid', 'appver'):
            setattr(self, option, self.get(fi, option))

        # Options that are only specified via caller input
        for option in ('inctran', 'incpos', 'incbal'):
            setattr(self, option, kwargs.get(option, True))

        for option in ('dtstart', 'dtend', 'dtasof'):
            setattr(self, option, kwargs.get(option, None))

        # Options where caller input overrides config
        bank_accts = []
        for accttype in ('checking', 'savings', 'moneymrkt', 'creditline'):
            accts  = kwargs.get(accttype, None) \
                    or parse_accts(self.get(fi, accttype))
            bank_accts += [(accttype.upper(), acct[0] or self.bankid, acct[1])
                            for acct in accts]
        self.bank_accounts = bank_accts
        self.creditcard_accounts = kwargs.get('creditcard', None) \
                or acct_re.findall(self.get(fi, 'creditcard'))
        inv_accts = kwargs.get('investment', None) or parse_accts(self.get(fi,'investment'))
        self.investment_accounts = [(acct[0] or self.brokerid, acct[1])
                    for acct in inv_accts]

        self.user = kwargs.get('user', None) or self.get(fi,'user')

    @property
    def client_config(self):
        return dict([(option, getattr(self, option))
            for option in ('url', 'org', 'fid', 'version', 'appid', 'appver')])

    @property
    def archive_dir(self):
        fi_dir = os.path.join(self.dir, self.fi)
        if not os.path.exists(fi_dir):
            os.makedirs(fi_dir)
        return fi_dir

def main():
    ### PARSE COMMAND LINE OPTIONS
    from getpass import getpass

    optparser = init_optionparser()

    # Process options & validate input
    (options, args) = optparser.parse_args()

    # Convert dtXXX str -> datetime.date
    dateconv = valid.validators.DateConverter(if_empty=None)
    for attr in ('dtstart', 'dtend', 'dtasof'):
        string = getattr(options, attr, None)
        setattr(options, attr, dateconv.to_python(string))

    # Parse account info
    for accttype in ('checking', 'savings', 'moneymrkt', 'creditline', 'investment'):
        string = getattr(options, accttype) or ''
        setattr(options, accttype, parse_accts(string))

    options.creditcard = acct_re.findall(options.creditcard or '')

    ### PARSE CONFIG
    config = OFXConfigParser()
    config.read(options.config)

    # If we're just listing known FIs, then bail out here.
    if options.list:
        print config.fi_index
        return

    if len(args) != 1:
        optparser.print_usage()
        return

    fi = args[0]
    if fi not in config.fi_index:
        # FIXME
        raise ValueError

    config.setup_fi(fi, **options.__dict__)
    client = OFXClient.from_config(**config.__dict__)
    # Don't ask for password until we're sure nothing's blown up
    user = config.user
    password = getpass()
    request = client.write_request(user, password)
    if options.dry_run:
        print request
        return

    response = client.download(archive_dir=config.archive_dir)
    print response.read()


if __name__ == '__main__':
    main()