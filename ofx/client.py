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

APP_DEFAULTS = {'version': '102', 'appid': 'QWIN', 'appver': '1800',}
FI_DEFAULTS = {'org': '', 'fid': '', 'bankid': '', 'brokerid': '', 'user': ''}
STMT_DEFAULTS = {'inctran': True, 'dtstart': None, 'dtend': None,
                'incpos': True, 'dtasof': None, 'incbal': True, }
ACCT_DEFAULTS = {'checking': '', 'savings': '', 'moneymrkt': '',
                'creditline': '', 'creditcard': '', 'investment': ''}
UI_DEFAULTS = {'list': False, 'dry_run': False, 'config': None,
                'archive': True, 'dir': None, 'user': ''}


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

    defaults = APP_DEFAULTS.copy()
    defaults.update(FI_DEFAULTS)
    defaults.update(STMT_DEFAULTS)

    overrides = {}

    def __init__(self, url, **kwargs):
        self.url = url
        for (name, value) in kwargs.iteritems():
            if name in self.defaults:
                if name in ('appid', 'appver'):
                    assert value in getattr(self, '%ss' % name)
                self.overrides[name] = value
        # Initialize
        self.reset()

    def reset(self):
        self.signon = None
        self.bank = None
        self.creditcard = None
        self.investment = None
        self.request = None
        self.response = None

    def __getattr__(self, name):
        try:
            return self.overrides.get(name, self.defaults[name])
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    @classmethod
    def from_config(cls, config):
        client_opts = dict([(k, getattr(config, k)) \
                        for k in APP_DEFAULTS.keys() + FI_DEFAULTS.keys()])
        client = cls(config.url, **client_opts)

        stmt_opts = dict([(k, getattr(config, k)) \
                        for k in STMT_DEFAULTS.keys()])
        for accttype in ('bank', 'creditcard'):
            accts = getattr(config, '%s_accounts' % accttype, None)
            if accts:
                write_method = getattr(client, 'write_%s' % accttype)
                write_method(accts, **stmt_opts)
        invaccts = getattr(config, 'investment_accounts', None)
        if invaccts:
            client.write_investment(invaccts, **stmt_opts)
        return client

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
            print err.info()
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
            print source.read()
            raise ValueError("OFX download errors: '%s'" % str(errors))

        if archive_dir:
            dtserver = ofxparser.signon.dtserver
            archive_path = os.path.join(archive_dir, '%s.ofx' % dtserver.strftime('%Y%m%d%H%M%S'))
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
        version = (int(self.version)/100)*100 # Int division drops remainder
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

    def write_bank(self, accounts, **kwargs):
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

            self.include_transactions(stmtrq, **kwargs)
        self.bank = msgsrq

    def write_creditcard(self, accounts, **kwargs):
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

            self.include_transactions(stmtrq, **kwargs)
        self.creditcard = msgsrq

    def write_investment(self, accounts, **kwargs):
        """ """
        if not accounts:
            # FIXME
            raise ValueError('No investment accounts requested')

        incpos = kwargs.get('incpos', self.incpos)
        dtasof = kwargs.get('dtasof', self.dtasof)
        incbal = kwargs.get('incbal', self.incbal)

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

            self.include_transactions(stmtrq, **kwargs)

            SubElement(stmtrq, 'INCOO').text = 'N'

            pos = SubElement(stmtrq, 'INCPOS')
            if dtasof:
                SubElement(pos, 'DTASOF').text = dtConverter.from_python(dtasof)
            SubElement(pos, 'INCLUDE').text = stringBool.from_python(incpos)

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

    def include_transactions(self, parent, **kwargs):
        include = kwargs.get('inctran', self.inctran)
        dtstart = kwargs.get('dtstart', self.dtstart)
        dtend = kwargs.get('dtend', self.dtend)

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
    defaults = UI_DEFAULTS.copy()
    defaults.update(STMT_DEFAULTS)
    defaults.update(ACCT_DEFAULTS)
    optparser.set_defaults(**defaults)
    optparser.add_option('-l', '--list', action='store_true',
                        help='list known institutions and exit')
    optparser.add_option('-n', '--dry-run', action='store_true',
                        help='display OFX request and exit')
    optparser.add_option('-f', '--config', metavar='FILE', help='use alternate config file')
    optparser.add_option('-r', '--no-archive', dest='archive', action='store_false',
                        help="don't archive OFX downloads to file")
    optparser.add_option('-o', '--dir', metavar='DIR', help='archive OFX downloads in DIR')
    optparser.add_option('-u', '--user', help='login user ID at institution')
    # Bank accounts
    bankgroup = OptionGroup(optparser, 'Bank accounts are specified as pairs of (routing#, acct#)')
    bankgroup.add_option('-c', '--checking', metavar='(LIST OF ACCOUNTS)')
    bankgroup.add_option('-a', '--savings', metavar='(LIST OF ACCOUNTS)')
    bankgroup.add_option('-m', '--moneymrkt', metavar='(LIST OF ACCOUNTS)')
    bankgroup.add_option('-y', '--creditline', metavar='(LIST OF ACCOUNTS)')
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
    transgroup.add_option('-t', '--no-transactions', dest='inctran',
                        action='store_false')
    transgroup.add_option('-s', '--start', dest='dtstart')
    transgroup.add_option('-e', '--end', dest='dtend')
    optparser.add_option_group(transgroup)
    # Position options
    posgroup = OptionGroup(optparser, '(Investment) Position Options')
    posgroup.add_option('-p', '--no-positions', dest='incpos',
                        action='store_false')
    posgroup.add_option('-d', '--date', dest='dtasof')
    optparser.add_option_group(posgroup)
    # Balance options
    balgroup = OptionGroup(optparser, '(Investment) Balance Options')
    balgroup.add_option('-b', '--no-balances', dest='incbal',
                        action='store_false')
    optparser.add_option_group(balgroup)

    return optparser


class OFXClientConfig(object):
    """ """
    main_config = _(os.path.join(os.path.dirname(__file__), 'main.cfg'))

    fallbacks = APP_DEFAULTS.copy()
    fallbacks.update(FI_DEFAULTS)
    fallbacks.update(ACCT_DEFAULTS)
    fallbacks.update(STMT_DEFAULTS)

    defaults = None
    overrides = {}

    def __init__(self):
        self.defaults = ConfigParser.SafeConfigParser(self.fallbacks)

    def __getattr__(self, name):
        # First check if we're looking up a global config
        if name in ('config', 'dir',):
            # FIXME - extend
            return _(self.defaults.get('global', name))
        # If we're looking up an FI config, we need to know which one.
        if 'fi' not in self.overrides:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, 'fi'))
        if name == 'fi':
            return self.overrides['fi']
        try:
            # This blows up inside ConfigParser
            #return self.overrides.get(name, self.defaults.get(self.fi, name))
            value = self.overrides.get(name, 'NO_DEFAULT')
            if value == 'NO_DEFAULT':
                value = self.defaults.get(self.fi, name)
            return value

        except ConfigParser.NoSectionError, ConfigParser.NoOptionError:
            raise AttributeError
            ("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if name in ('defaults', 'overrides'):
            object.__setattr__(self, name, value)
        else:
            self.overrides[name] = value

    def read(self, filenames=None):
        defaults = self.defaults
        # Load main config
        defaults.readfp(open(self.main_config))
        # Then load user configs (defaults to main.cfg [global] config: value)
        filenames = filenames or _(defaults.get('global', 'config'))
        return defaults.read(filenames)

    @property
    def fi_index(self):
        sections = self.defaults.sections()
        sections.remove('global')
        return sections

    @property
    def bank_accounts(self):
        bank_accts = []
        for accttype in ('checking', 'savings', 'moneymrkt', 'creditline'):
            accts  = parse_accts(getattr(self, accttype))
            bank_accts += [(accttype.upper(), acct[0] or self.bankid, acct[1])
                            for acct in accts]
        return bank_accts

    @property
    def creditcard_accounts(self):
        return acct_re.findall(self.creditcard)

    @property
    def investment_accounts(self):
        brokerid = self.brokerid
        return [(brokerid, acct) for acct in acct_re.findall(self.investment)]

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

    # Transform options into a dict for ease of further processing
    options = options.__dict__

    # Demux UI-only opts
    ui_opts = dict([(k,options.pop(k)) for k in UI_DEFAULTS.keys()])

    ### PARSE CONFIG
    config = OFXClientConfig()
    config.read(ui_opts['config'])

    # If we're just listing known FIs, then bail out here.
    if ui_opts['list']:
        print config.fi_index
        return

    if len(args) != 1:
        optparser.print_usage()
        return
    config.fi = args[0]

    # Override user config, if optparser field is non-empty.
    config.user = ui_opts.pop('user') or config.user

    # Demux acct#s and override config files if not empty.
    for k in ACCT_DEFAULTS.keys():
        config.overrides[k] = options.pop(k) or getattr(config, k)

    # Only statement opts should remain to demux.  These should clobber
    # configs, since they're not supposed to be specified in config files.
    dateconv = valid.validators.DateConverter(if_empty=None)
    for k in STMT_DEFAULTS.keys():
        v = options.pop(k)
        if k[:2] == 'dt':
            v = dateconv.to_python(v)
        config.overrides[k] = v

    client = OFXClient.from_config(config)
    # Don't ask for password until we're sure nothing's blown up
    user = config.user
    password = getpass()
    request = client.write_request(user, password)
    if ui_opts['dry_run']:
        print request
        return

    if ui_opts['archive']:
        archive_dir = _(ui_opts['dir'] or config.archive_dir)
    else:
        archive_dir = None

    response = client.download(archive_dir=archive_dir)
    import sys
    sys.exit()
    if not ui_opts['archive']:
        print response.read()


if __name__ == '__main__':
    main()