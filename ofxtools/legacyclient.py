#!/usr/bin/env python
# vim: set fileencoding=utf-8
"""
Classes and functions implementing composing and transmitting OFX request,
and receiving OFX responses in reply
"""

# stdlib imports
import sys
import datetime
import uuid
import xml.etree.ElementTree as ET
from collections import OrderedDict
from os import path
import re
from getpass import getpass


PYTHON_VERSION = sys.version_info.major

if PYTHON_VERSION == 3:
    from configparser import SafeConfigParser
    from urllib.request import urlopen, HTTPError
    from urllib.parse import urlparse
    from io import StringIO
else:
    from ConfigParser import SafeConfigParser
    from urllib2 import urlopen, HTTPError
    from urlparse import urlparse
    from StringIO import StringIO


# 3rd party imports
import requests


# local imports
from ofxtools.header import OFXHeader
from ofxtools.Types import Bool, OneOf, DateTime
from ofxtools.utils import fixpath
from ofxtools.models.bank import ACCTTYPES


class BankAcct(object):
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
        accttype = OneOf(*ACCTTYPES).convert(accttype)
        self._acct['ACCTTYPE'] = OneOf(*ACCTTYPES).convert(accttype)

        bankid = str(bankid)
        if not self.routingre.match(bankid):
            raise ValueError('Invalid bankid %s' % bankid)
        self._acct['BANKID'] = bankid

        assert acctid
        self._acct['ACCTID'] = str(acctid)

    def __repr__(self):
        values = [v for v in self._acct.values()]
        repr_string = '%s(' + ', '.join(["'%s'"]*len(values)) + ')'
        values.insert(0, self.__class__.__name__)
        return repr_string % tuple(values)

    def stmtrq(self, inctran=True, dtstart=None, dtend=None, **kwargs):
        """ """
        # **kwargs catches incpos/dtasof
        # Requesting transactions without dtstart/dtend (which is the default)
        # asks for all transactions on record.
        rq = ET.Element(self.stmtrq_tag)
        rq.append(self.acctfrom)
        rq.append(self.inctran(inctran, dtstart, dtend))
        return rq

    @property
    def acctfrom(self):
        """ """
        acctfrom = ET.Element(self.acctfrom_tag)
        for tag, text in self._acct.items():
            ET.SubElement(acctfrom, tag).text = text
        return acctfrom

    def inctran(self, inctran, dtstart, dtend):
        """ """
        tran = ET.Element('INCTRAN')
        if dtstart:
            ET.SubElement(tran, 'DTSTART').text = DateTime().unconvert(dtstart)
        if dtend:
            ET.SubElement(tran, 'DTEND').text = DateTime().unconvert(dtend)
        ET.SubElement(tran, 'INCLUDE').text = Bool().unconvert(inctran)
        return tran


class CcAcct(BankAcct):
    """ """
    acctkeys = ('ACCTID',)
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
        oo = ET.Element('INCOO')
        oo.text = Bool().unconvert(False)
        return oo

    def incpos(self, dtasof, incpos):
        pos = ET.Element('INCPOS')
        if dtasof:
            ET.SubElement(pos, 'DTASOF').text = DateTime().unconvert(dtasof)
        ET.SubElement(pos, 'INCLUDE').text = Bool().unconvert(incpos)
        return pos

    def incbal(self, incbal):
        bal = ET.Element('INCBAL')
        bal.text = Bool().unconvert(incbal)
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

    def __init__(self, url, org, fid, version=None, appid=None, appver=None,
                 clientuid=None):
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
        if clientuid:
            self.clientuid = str(clientuid)

    @property
    def ofxheader(self):
        """ Prepend to OFX markup. """
        return str(OFXHeader(version=self.version, newfileuid=uuid.uuid4()))

    def signon(self, user, password, clientuid=None):
        msgsrq = ET.Element('SIGNONMSGSRQV1')
        sonrq = ET.SubElement(msgsrq, 'SONRQ')
        ET.SubElement(sonrq, 'DTCLIENT').text = DateTime().unconvert(datetime.datetime.now())
        ET.SubElement(sonrq, 'USERID').text = user
        ET.SubElement(sonrq, 'USERPASS').text = password
        ET.SubElement(sonrq, 'LANGUAGE').text = 'ENG'
        if self.org:
            fi = ET.SubElement(sonrq, 'FI')
            ET.SubElement(fi, 'ORG').text = self.org
            if self.fid:
                ET.SubElement(fi, 'FID').text = self.fid
        ET.SubElement(sonrq, 'APPID').text = self.appid
        ET.SubElement(sonrq, 'APPVER').text = str(self.appver)
        if clientuid:
            ET.SubElement(sonrq, 'CLIENTUID').text = clientuid
        return msgsrq

    def statement_request(self, user, password, accounts, clientuid=None,
                          **kwargs):
        """ """
        ofx = ET.Element('OFX')
        ofx.append(self.signon(user, password, clientuid))

        # Create MSGSRQ SubElements for each acct type, indexed by tag
        msgsrq_tags = [getattr(a, 'msgsrq_tag') for a in (BankAcct, CcAcct, InvAcct)]
        msgsrqs = {tag: ET.SubElement(ofx, tag) for tag in msgsrq_tags}

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
        ofx = ET.Element('OFX')
        ofx.append(self.signon(user, password))
        msgsrq = ET.SubElement(ofx, 'PROFMSGSRQV1')
        profrq = ET.Element('PROFRQ')
        ET.SubElement(profrq, 'CLIENTROUTING').text = 'NONE'
        ET.SubElement(profrq, 'DTPROFUP').text = DateTime().unconvert(datetime.date(1990,1,1))
        msgsrq.append(self._wraptrn(profrq))
        return ofx

    def download(self, request):
        """ """
        # py3k: ElementTree.tostring() returns bytes not str
        data = self.ofxheader + ET.tostring(request).decode()

        mimetype = 'application/x-ofx'
        headers = {'Content-type': mimetype, 'Accept': '*/*, %s' % mimetype}

        try:
            response = requests.post(self.url, data=data, headers=headers)
            return StringIO(response.text)
        except HTTPError as err:
            # FIXME
            print(err.info())
            raise

    def _wraptrn(self, rq):
        """ """
        tag = rq.tag
        assert 'TRNRQ' not in tag
        assert tag[-2:] == 'RQ'
        trnrq = ET.Element(tag.replace('RQ', 'TRNRQ'))
        ET.SubElement(trnrq, 'TRNUID').text = str(uuid.uuid4())
        trnrq.append(rq)
        return trnrq


### CLI COMMANDS
def do_stmt(args):
    client = OFXClient(args.url, args.org, args.fid, version=args.version,
                       appid=args.appid, appver=args.appver,
                       clientuid=args.clientuid)

    # Define accounts
    accts = []
    for accttype in ('checking', 'savings', 'moneymrkt', 'creditline'):
        for acctid in getattr(args, accttype):
            a = BankAcct(args.bankid, acctid, accttype)
            accts.append(a)

    for acctid in args.creditcard:
        accts.append(CcAcct(acctid))

    for acctid in args.investment:
        accts.append(InvAcct(args.brokerid, acctid))

    # Use dummy password for dummy request
    if args.dry_run:
        password = 'T0PS3CR3T'
    else:
        password = getpass()

    # Statement parameters
    d = vars(args)
    # convert dtstart/dtend/dtasof from str to datetime
    kwargs = {k: DateTime().convert(v) for k, v in d.items() if k.startswith('dt')}
    # inctrans/incpos/incbal
    kwargs.update({k: v for k, v in d.items() if k.startswith('inc')})
    # clientuid
    if 'clientuid' in d:
        kwargs['clientuid'] = d['clientuid']

    request = client.statement_request(args.user, password, accts, **kwargs)

    # Handle request
    if args.dry_run:
        print(client.ofxheader + ET.tostring(request).decode())
    else:
        response = client.download(request)
        print(response.getvalue())


class OFXConfigParser(SafeConfigParser):
    """ """
    fi_config = path.join(path.dirname(__file__), 'config', 'fi.cfg')

    def __init__(self):
        SafeConfigParser.__init__(self)

    def read(self, filenames=None):
        # Load FI config
        self.readfp(open(fixpath(self.fi_config)))
        # Then load user configs (defaults to fi.cfg [global] config: value)
        filenames = filenames or fixpath(self.get('global', 'config'))
        return SafeConfigParser.read(self, filenames)

    @property
    def fi_index(self):
        sections = self.sections()
        sections.remove('global')
        return sections


def main():
    # Read config first, so fi_index can be used in help
    config = OFXConfigParser()
    config.read()

    from argparse import ArgumentParser

    argparser = ArgumentParser(description='Download OFX financial data',
                               epilog='FIs configured: %s' % config.fi_index)
    argparser.add_argument('server', help='OFX server - URL or FI name from config')
    argparser.add_argument('-n', '--dry-run', action='store_true',
                           default=False, help='display OFX request and exit')

    signon_group = argparser.add_argument_group(title='Signon Options')
    signon_group.add_argument('-u', '--user', help='FI login username')
    signon_group.add_argument('--org', help='FI.ORG')
    signon_group.add_argument('--fid', help='FI.FID')
    signon_group.add_argument('--version', help='OFX version')
    signon_group.add_argument('--appid', help='OFX client app identifier')
    signon_group.add_argument('--appver', help='OFX client app version')
    signon_group.add_argument('--clientuid', help='OFX client UID')

    acct_group = argparser.add_argument_group(title='Account Options')
    acct_group.add_argument('--bankid', help='ABA routing#')
    acct_group.add_argument('--brokerid', help='Broker ID string')
    acct_group.add_argument('-C', '--checking', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-S', '--savings', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-M', '--moneymrkt', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-L', '--creditline', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-c', '--creditcard', '--cc', metavar='acct#', action='append', default=[])
    acct_group.add_argument('-i', '--investment', metavar='acct#', action='append', default=[])

    stmt_group = argparser.add_argument_group(title='Statement Options')
    stmt_group.add_argument('-s', '--start', dest='dtstart',
                            help='(YYYYmmdd) Transactions list start date')
    stmt_group.add_argument('-e', '--end', dest='dtend',
                            help='(YYYYmmdd) Transactions list end date')
    stmt_group.add_argument('-d', '--date', dest='dtasof',
                            help='(YYYYmmdd) As-of date for investment positions')
    stmt_group.add_argument('--no-transactions', dest='inctran',
                            action='store_false', default=True,
                            help='Omit transactions list')
    stmt_group.add_argument('--no-positions', dest='incpos',
                            action='store_false', default=True,
                            help='Omit investment positions')
    stmt_group.add_argument('--no-balances', dest='incbal',
                            action='store_false', default=True,
                            help='Omit balances')

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
        overrides = [k for k, v in vars(args).items() if v]
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

    # Pass the parsed args to the statement-request function
    do_stmt(args)


if __name__ == '__main__':
    main()
