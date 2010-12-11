#!/usr/bin/python2.7
import sys
import datetime
import uuid
from xml.etree.cElementTree import Element, SubElement, tostring
import contextlib
import urllib2
import os
import ConfigParser
from cStringIO import StringIO
import re
from getpass import getpass

from utilities import _, OFXDtConverter, OFXStringBool, BankAcctTypeValidator, OFXv1, OFXv2, prettify

if sys.version_info < (2, 7):
    raise RuntimeError('ofx.client library requires Python v2.7+')

VERSIONS = OFXv1 + OFXv2

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

#APP_DEFAULTS = {'version': '102', 'appid': 'QWIN', 'appver': '1800',}
#FI_DEFAULTS = {'url': '', 'org': '', 'fid': '', 'bankid': '', 'brokerid': '',}
#ACCT_DEFAULTS = {'checking': '', 'savings': '', 'moneymrkt': '',
                #'creditline': '', 'creditcard': '', 'investment': '',}
#STMT_DEFAULTS = {'inctran': True, 'dtstart': None, 'dtend': None,
                #'incpos': True, 'dtasof': None, 'incbal': True, }

class OFXClient(object):
    """ """
    defaults = {'version': '102', 'appid': 'QWIN', 'appver': '1800',
                'url': None, 'org': None, 'fid': None,
                'bankid': None, 'brokerid': None,
    }

    stmt_defaults = {'inctran': True, 'dtstart': None, 'dtend': None,
                    'incpos': True, 'dtasof': None, 'incbal': True,
    }

    acct_defaults = {'checking': '', 'savings': '', 'moneymrkt': '',
                    'creditline': '', 'creditcard': '', 'investment': '',}

    acct_re = re.compile(r'([\w.\-/]{1,22})')
    bankpair_re = re.compile(r'\(([\w.\-/]{1,9}),\s*([\w.\-/]{1,22})\)')
    pair_re = re.compile(r'\(([\w.\-/]{1,22}),\s*([\w.\-/]{1,22})\)')
    naked_re = re.compile(r'(\b)([\w.\-/]{1,22})')

    def __init__(self, url, org=defaults['org'], fid=defaults['fid'],
                bankid=defaults['bankid'], brokerid=defaults['brokerid'],
                version=defaults['version'],
                appid=defaults['appid'], appver=defaults['appver']):
        self.url = url
        self.org = org; self.fid = fid
        self.bankid=bankid; self.brokerid = brokerid
        self.version = version; self.appid = appid; self.appver = appver

        # Initialize
        self.reset()

    @classmethod
    def from_args(cls, args):
        """
        Create an OFXClient from output of argparse.ArgumentParser.parse_args().
        Extraneous args not related to FI-specific settings are ignored.
        """
        return cls(**{k: getattr(args, k) for k in cls.defaults.iterkeys()})

    def reset(self):
        self.signon = None
        self.bank = None
        self.creditcard = None
        self.investment = None
        self.ofx = None
        self.request = None
        self.response = None

    def download(self, user=None, password=None):
        mimetype = 'application/x-ofx'
        headers = {'Content-type': mimetype, 'Accept': '*/*, %s' % mimetype}
        if not self.request:
            self.write_request(user, password)
        http = urllib2.Request(self.url, self.request, headers)
        try:
            with contextlib.closing(urllib2.urlopen(http)) as response:
                # urllib2.urlopen returns an addinfourl instance, which supports
                # a limited subset of file methods.  Copy response to a StringIO
                # so that we can use tell() and seek().
                source = StringIO()
                source.write(response.read())
                # After writing, rewind to the beginning.
                source.seek(0)
                self.response = source
                return source
        except urllib2.HTTPError as err:
            # FIXME
            print err.info()
            raise

    def write_request(self, user=None, password=None):
        ofx = self.ofx = Element('OFX')
        if not self.signon:
            self.request_signon(user, password)
        ofx.append(self.signon)
        for msgset in ('bank', 'creditcard', 'investment'):
            msgset = getattr(self, msgset, None)
            if msgset:
                ofx.append(msgset)
        self.request = request = self.header + tostring(ofx)
        return request

    def request_profile(self, user=None, password=None):
        user = user or 'elmerfudd'
        password = password or 'TOPSECRET'
        self.request_signon(user, password)
        ofx = Element('OFX')
        ofx.append(self.signon)
        msgsrq = Element('PROFMSGSRQV1')
        profrq = self.wrap_request(msgsrq, 'PROFRQ')
        SubElement(profrq, 'CLIENTROUTING').text = 'NONE'
        SubElement(profrq, 'DTPROFUP').text = OFXDtConverter.from_python(datetime.date(1990,1,1))
        ofx.append(msgsrq)
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

    def request_signon(self, user, password):
        if not (user and password):
            # FIXME
            raise ValueError
        msgsrq = Element('SIGNONMSGSRQV1')
        sonrq = SubElement(msgsrq, 'SONRQ')
        SubElement(sonrq, 'DTCLIENT').text = OFXDtConverter.from_python(datetime.datetime.now())
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

    def request_bank(self, accounts, inctran=stmt_defaults['inctran'],
                        dtstart=stmt_defaults['dtstart'], dtend=stmt_defaults['dtend']):
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
                accttype = BankAcctTypeValidator.to_python(accttype)
            except ValueError:
                # FIXME
                raise ValueError("Bank accounts must be specified as a sequence of (ACCTTYPE, BANKID, ACCTID) tuples, not '%s'" % str(accounts))
            assert bankid
            stmtrq = self.wrap_request(msgsrq, 'STMTRQ')
            acctfrom = SubElement(stmtrq, 'BANKACCTFROM')
            SubElement(acctfrom, 'BANKID').text = bankid
            SubElement(acctfrom, 'ACCTID').text = acctid
            SubElement(acctfrom, 'ACCTTYPE').text = accttype

            self._include_transactions(stmtrq, inctran, dtstart, dtend)
        self.bank = msgsrq

    def request_creditcard(self, accounts, inctran=stmt_defaults['inctran'],
                        dtstart=stmt_defaults['dtstart'], dtend=stmt_defaults['dtend']):
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

            self._include_transactions(stmtrq, inctran, dtstart, dtend)
        self.creditcard = msgsrq

    def request_investment(self, accounts, inctran=stmt_defaults['inctran'],
                        dtstart=stmt_defaults['dtstart'], dtend=stmt_defaults['dtend'],
                        incpos=stmt_defaults['incpos'], dtasof=stmt_defaults['dtasof'],
                        incbal=stmt_defaults['incbal']):
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
            assert brokerid

            stmtrq = self.wrap_request(msgsrq, 'INVSTMTRQ')
            acctfrom = SubElement(stmtrq, 'INVACCTFROM')

            SubElement(acctfrom, 'BROKERID').text = brokerid
            SubElement(acctfrom, 'ACCTID').text = acctid

            self._include_transactions(stmtrq, inctran, dtstart, dtend)

            SubElement(stmtrq, 'INCOO').text = 'N'
            pos = SubElement(stmtrq, 'INCPOS')
            if dtasof:
                SubElement(pos, 'DTASOF').text = OFXDtConverter.from_python(dtasof)
            SubElement(pos, 'INCLUDE').text = OFXStringBool.from_python(incpos)

            SubElement(stmtrq, 'INCBAL').text = OFXStringBool.from_python(incbal)
        self.investment = msgsrq

    def request_all(self, bank_accts, cc_accts, inv_accts, inctran=stmt_defaults['inctran'],
                        dtstart=stmt_defaults['dtstart'], dtend=stmt_defaults['dtend'],
                        incpos=stmt_defaults['incpos'], dtasof=stmt_defaults['dtasof'],
                        incbal=stmt_defaults['incbal']):
        if bank_accts:
            self.request_bank(bank_accts, inctran, dtstart, dtend)
        if cc_accts:
            self.request_creditcard(cc_accts, inctran, dtstart, dtend)
        if inv_accts:
            self.request_investment(inv_accts, inctran, dtstart, dtend, incpos, dtasof, incbal)

    # Utilities
    def wrap_request(self, parent, tag):
        """ """
        assert 'TRNRQ' not in tag
        assert tag[-2:] == 'RQ'
        trnrq = SubElement(parent, tag.replace('RQ', 'TRNRQ'))
        SubElement(trnrq, 'TRNUID').text = str(uuid.uuid4())
        return SubElement(trnrq, tag)

    def _include_transactions(self, parent, inctran, dtstart, dtend):
        element = SubElement(parent, 'INCTRAN')
        if dtstart:
            SubElement(element, 'DTSTART').text = OFXDtConverter.from_python(dtstart)
        if dtend:
            SubElement(element, 'DTEND').text = OFXDtConverter.from_python(dtend)
        SubElement(element, 'INCLUDE').text = OFXStringBool.from_python(inctran)
        return element

    def parse_bank(self, accttype, string):
        # FIXME - it would be nice to be able to mix&match the two styles
        # within a single line.
        accts = self.bankpair_re.findall(string) or self.naked_re.findall(string)
        return [(accttype.upper(), acct[0] or self.bankid, acct[1])
                for acct in accts]

    def parse_cc(self, string):
        return self.acct_re.findall(string)

    def parse_inv(self, string):
        return [(self.brokerid, acct) for acct in self.acct_re.findall(string)]

    def parse_account_strings(self, checking=None, savings=None,
        moneymrkt=None, creditline=None, creditcard=None, investment=None):
        checking = checking or ''
        savings = savings or ''
        moneymrkt = moneymrkt or ''
        creditline = creditline or ''
        creditcard = creditcard or ''
        investment = investment or ''
        bank_accts = []
        bank_accts += self.parse_bank('checking', checking)
        bank_accts += self.parse_bank('savings', savings)
        bank_accts += self.parse_bank('moneymrkt', moneymrkt)
        bank_accts += self.parse_bank('creditline', creditline)
        cc_accts = self.parse_cc(creditcard)
        inv_accts = self.parse_inv(investment)
        return bank_accts, cc_accts, inv_accts


class OFXConfigParser(ConfigParser.SafeConfigParser):
    """ """
    main_config = _(os.path.join(os.path.dirname(__file__), 'main.cfg'))

    defaults = OFXClient.defaults.copy()
    defaults.update(OFXClient.acct_defaults)

    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self, self.defaults)

    def read(self, filenames=None):
        # Load main config
        self.readfp(open(self.main_config))
        # Then load user configs (defaults to main.cfg [global] config: value)
        filenames = filenames or _(self.get('global', 'config'))
        return ConfigParser.SafeConfigParser.read(self, filenames)

    @property
    def fi_index(self):
        sections = self.sections()
        sections.remove('global')
        return sections


def init_argparser():
    from argparse import ArgumentParser, SUPPRESS

    #usage = "usage: %(prog)s [options] institution"
    #argparser = ArgumentParser(usage=usage)
    root_parser = ArgumentParser(description='Download OFX financial data')

    subparsers = root_parser.add_subparsers()
    list_subparser = subparsers.add_parser('list', help='List known FIs and exit')
    list_subparser.set_defaults(func=do_list)

    detail_subparser = subparsers.add_parser('detail', help='Show FI configuration and exit')
    detail_subparser.add_argument('fi')
    detail_subparser.set_defaults(func=do_detail)

    request_subparser = ArgumentParser(add_help=False)

    request_subparser.add_argument('-U', '--url', default=SUPPRESS,
                                    help='FI web address')
    request_subparser.add_argument('-u', '--user', default=SUPPRESS,
                                    help='FI login username')
    request_subparser.add_argument('--version', default=SUPPRESS,
                                    help='OFX version')
    request_subparser.add_argument('--appid', default=SUPPRESS,
                                    help='Application identifier string')
    request_subparser.add_argument('--appver', default=SUPPRESS,
                                    help='Application version number')
    request_subparser.add_argument('--org', default=SUPPRESS,
                                    help='FI.ORG')
    request_subparser.add_argument('--fid', default=SUPPRESS,
                                    help='FI.FID')
    request_subparser.add_argument('--bankid', default=SUPPRESS,
                                    help='ABA routing#')
    request_subparser.add_argument('--brokerid', default=SUPPRESS,
                                    help='Broker ID string')
    request_subparser.add_argument('-n', '--dry-run', action='store_true',
                                    #default=SUPPRESS,
                                    default=False,
                                    help='display OFX request and exit')

    profile_subparser= subparsers.add_parser('profile', parents=[request_subparser], help='Download OFX profile')
    profile_subparser.add_argument('fi', nargs='?', help="Name of FI configuration section ('list' subcommand shows known FIs)")
    profile_subparser.set_defaults(func=do_profile)

    stmt_subparser = subparsers.add_parser('stmt', parents=[request_subparser], help='Download OFX statement')
    stmt_subparser.add_argument('fi', nargs='?', help="Name of FI configuration section ('list' subcommand shows known FIs)")

    # Accounts
    acct_group = stmt_subparser.add_argument_group(title='Account Options')
    acct_group.add_argument('-C', '--checking', nargs='+',
                            default=SUPPRESS, metavar='(routing#, acct#)')
    acct_group.add_argument('-S', '--savings', nargs='+',
                            default=SUPPRESS, metavar='(routing#, acct#)')
    acct_group.add_argument('-M', '--moneymrkt', nargs='+',
                            default=SUPPRESS, metavar='(routing#, acct#)')
    acct_group.add_argument('-L', '--creditline', nargs='+',
                            default=SUPPRESS, metavar='(routing#, acct#)')
    acct_group.add_argument('-c', '--cc', '--creditcard', nargs='+',
                            default=SUPPRESS, metavar='(acct#)')
    acct_group.add_argument('-i', '--investment', nargs='+',
                            default=SUPPRESS, metavar='(acct#)')

    # Statement options
    stmt_group = stmt_subparser.add_argument_group(title='Statement Options')
    stmt_group.add_argument('-s', '--start', dest='dtstart', help='Start date/time for transactions')
    stmt_group.add_argument('-e', '--end', dest='dtend', help='End date/time for transactions')
    stmt_group.add_argument('--no-transactions', dest='inctran',
                            action='store_false', default=True)
    stmt_group.add_argument('-d', '--date', dest='dtasof', help='As-of date for investment positions')
    stmt_group.add_argument('--no-positions', dest='incpos',
                            action='store_false', default=True)
    stmt_group.add_argument('--no-balances', dest='incbal',
                            action='store_false', default=True)

    stmt_group.set_defaults(func=do_stmt)

    return root_parser


def main():
    config = OFXConfigParser()
    config.read()

    argparser = init_argparser()
    args = argparser.parse_args()
    args.func(args, config)

def do_list(args, config):
    print str(config.fi_index)

def do_detail(args, config):
    # FIXME
    if args.fi not in config.fi_index:
        raise ValueError("Unknown FI '%s' not in %s"
                        % (fi, str(config.fi_index)))
    print str(dict(config.items(fi)))

def merge_config(args, config, stmt=False):
    fi = args.fi
    if fi:
        if fi not in config.fi_index:
            raise ValueError("Unknown FI '%s' not in %s"
                            % (fi, str(config.fi_index)))
        # Load values from config where CLI hasn't overridden them
        keys = OFXClient.defaults.keys() + ['user',]
        if stmt:
            keys += OFXClient.stmt_defaults.keys() \
            + OFXClient.acct_defaults.keys()
        for k in keys:
            if k not in args:
                setattr(args, k, config.get(fi, k))
    return args

def do_profile(args, config):
    # FIXME
    args = merge_config(args, config)
    client = OFXClient.from_args(args)

    if args.dry_run:
        client.write_request(user, 'TOPSECRET')
        print client.header + prettify(tostring(client.ofx))
        return

    args.password = getpass()
    client.request_profile(user=args.user, password=args.password)
    response = client.download()
    print response.read()

def do_stmt(args, config):
    args = merge_config(args, config, stmt=True)

    # Datetime validation/conversion
    for dt in ('dtstart', 'dtend', 'dtasof'):
        setattr(args, dt, OFXDtConverter.to_python(getattr(args, dt)))

    client = OFXClient.from_args(args)

    ### CONSTRUCT STATEMENT REQUESTS
    accts = {k: getattr(args, k) for k in ('checking', 'savings',
                'moneymrkt', 'creditline', 'creditcard', 'investment')}
    acct_tuple = client.parse_account_strings(**accts)
    stmt_options = {k: getattr(args, k) for k in client.stmt_defaults.iterkeys()}
    client.request_all(*acct_tuple, **stmt_options)

    ### HANDLE REQUEST
    if args.dry_run:
        client.write_request(user=args.user, password='TOPSECRET')
        print client.header + prettify(tostring(client.ofx))
        return

    args.password = getpass()
    client.write_request(user=args.user, password=args.password)

    response = client.download()
    print response.read()


if __name__ == '__main__':
    main()
