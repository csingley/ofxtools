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
from configparser import SafeConfigParser
from getpass import getpass

import converters
from utilities import _


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


class OFXConfigParser(SafeConfigParser):
    """ """
    main_config = _(os.path.join(os.path.dirname(__file__), 'main.cfg'))

    def __init__(self):
        SafeConfigParser.__init__(self)

    def read(self, filenames=None):
        # Load main config
        self.readfp(open(self.main_config))
        # Then load user configs (defaults to main.cfg [global] config: value)
        filenames = filenames or _(self.get('global', 'config'))
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
            print(accts)
            a = BankAcct(args.bankid, acctid, accttype)
            print(accts)
            print(a)
            accts.append(a)
            print(accts)
            print()

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

