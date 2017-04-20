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
from collections import namedtuple
from os import path
from getpass import getpass


PYTHON_VERSION = sys.version_info.major

if PYTHON_VERSION == 3:
    from configparser import SafeConfigParser
    from io import StringIO
else:
    from ConfigParser import SafeConfigParser
    from StringIO import StringIO


# 3rd party imports
import requests


# local imports
from ofxtools.header import OFXHeader
from ofxtools.models.ofx import OFX
from ofxtools.models.profile import (
    PROFRQ, PROFTRNRQ, PROFMSGSRQV1,
)
from ofxtools.models.signon import (
    SIGNONMSGSRQV1, SONRQ, FI,
)
from ofxtools.models.bank import (
    BANKMSGSRQV1, STMTTRNRQ, STMTRQ, BANKACCTFROM, CCACCTFROM, INCTRAN,
)
from ofxtools.models.creditcard import (
    CREDITCARDMSGSRQV1, CCSTMTTRNRQ, CCSTMTRQ,
)
from ofxtools.models.investment import (
    INVSTMTMSGSRQV1, INVSTMTTRNRQ, INVSTMTRQ, INVACCTFROM, INCPOS,
)
from ofxtools.Types import DateTime
from ofxtools.utils import fixpath


# Statement request data containers
# Pass sequences of these containers as args to OFXClient.request_statement()
StmtRq = namedtuple('StmtRq', ['acctid', 'accttype', 'dtstart', 'dtend',
                               'inctran'])
StmtRq.__new__.__defaults__ = (None, None, None, None, True)

CcStmtRq = namedtuple('CcStmtRq', ['acctid', 'dtstart', 'dtend', 'inctran'])
CcStmtRq.__new__.__defaults__ = (None, None, None, True)

InvStmtRq = namedtuple('InvStmtRq', ['acctid', 'dtstart', 'dtend', 'dtasof',
                                     'inctran', 'incoo', 'incpos', 'incbal'])
InvStmtRq.__new__.__defaults__ = (None, None, None, None, True, False, True,
                                  True)


class OFXClient:
    """ """
    # OFX header/signon defaults
    clientuid = None
    org = None
    fid = None
    version = 203
    appid = 'QWIN'
    appver = '2300'
    language = 'ENG'

    # Stmt request
    bankid = None
    brokerid = None

    def __init__(self, url,  org=None, fid=None, version=None, appid=None,
                 appver=None, language=None, bankid=None, brokerid=None):
        self.url = url
        if org is not None:
            self.org = org
        if fid is not None:
            self.fid = fid
        if version is not None:
            self.version = int(version)
        if appid is not None:
            self.appid = appid
        if appver is not None:
            self.appver = str(appver)
        if language is not None:
            self.language = language
        self.bankid = bankid
        self.brokerid = brokerid

    @property
    def ofxheader(self):
        """ Prepend to OFX markup. """
        return str(OFXHeader(version=self.version, newfileuid=uuid.uuid4()))

    def request_statements(self, user, password, clientuid=None,
                           stmtrqs=None, ccstmtrqs=None, invstmtrqs=None,
                           dryrun=False):
        """
        Input *rqs are sequences of the corresponding namedtuples
        (StmtRq, CcStmtRq, InvStmtRq)
        """
        signonmsgs = self.signon(user, password, clientuid=clientuid)

        bankmsgs = None
        if stmtrqs is not None:
            # bankid comes from OFXClient instance attribute,
            # not StmtRq namedtuple
            stmttrnrqs = [self.stmttrnrq(
                **dict(stmtrq._asdict(), bankid=self.bankid))
                for stmtrq in stmtrqs]
            bankmsgs = BANKMSGSRQV1(*stmttrnrqs)

        creditcardmsgs = None
        if ccstmtrqs is not None:
            ccstmttrnrqs = [self.ccstmttrnrq(**stmtrq._asdict())
                            for stmtrq in ccstmtrqs]
            creditcardmsgs = CREDITCARDMSGSRQV1(*ccstmttrnrqs)

        invstmtmsgs = None
        if invstmtrqs is not None:
            # brokerid comes from OFXClient instance attribute,
            # not StmtRq namedtuple
            invstmttrnrqs = [self.invstmttrnrq(
                **dict(stmtrq._asdict(), brokerid=self.brokerid))
                for stmtrq in invstmtrqs]
            invstmtmsgs = INVSTMTMSGSRQV1(*invstmttrnrqs)

        ofx = OFX(signonmsgsrqv1=signonmsgs,
                  bankmsgsrqv1=bankmsgs,
                  creditcardmsgsrqv1=creditcardmsgs,
                  invstmtmsgsrqv1=invstmtmsgs)

        if dryrun:
            return ofx
        return self.download(ofx)

    def request_profile(self, user=None, password=None, dryrun=False):
        """ """
        dtprofup = datetime.date(1990, 1, 1)
        profrq = PROFRQ(clientrouting='NONE', dtprofup=dtprofup)
        trnuid = uuid.uuid4()
        proftrnrq = PROFTRNRQ(trnuid=trnuid, profrq=profrq)
        msgs = PROFMSGSRQV1(proftrnrq)

        user = user or 'elmerfudd'
        password = password or 'TOPSECRET'
        signonmsgs = self.signon(user, password)

        ofx = OFX(signonmsgsrqv1=signonmsgs, profmsgsrqv1=msgs)

        if dryrun:
            return ofx
        return self.download(ofx)

    def signon(self, userid, userpass, sesscookie=None, clientuid=None):
        if self.org:
            fi = FI(org=self.org, fid=self.fid)
        else:
            fi = None

        dtclient = datetime.datetime.now()
        sonrq = SONRQ(dtclient=dtclient, userid=userid, userpass=userpass,
                      language=self.language, fi=fi, sesscookie=sesscookie,
                      appid=self.appid, appver=self.appver,
                      clientuid=clientuid)
        return SIGNONMSGSRQV1(sonrq=sonrq)

    def stmttrnrq(self, bankid, acctid, accttype, dtstart=None, dtend=None,
                  inctran=True):
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = STMTRQ(bankacctfrom=acct, inctran=inctran)
        trnuid = uuid.uuid4()
        return STMTTRNRQ(trnuid=trnuid, stmtrq=stmtrq)

    def ccstmttrnrq(self, acctid, dtstart=None, dtend=None, inctran=True):
        acct = CCACCTFROM(acctid=acctid)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = CCSTMTRQ(ccacctfrom=acct, inctran=inctran)
        trnuid = uuid.uuid4()
        return CCSTMTTRNRQ(trnuid=trnuid, ccstmtrq=stmtrq)

    def invstmttrnrq(self, acctid, brokerid,
                     dtstart=None, dtend=None, inctran=True, incoo=False,
                     dtasof=None, incpos=True, incbal=True):
        acct = INVACCTFROM(acctid=acctid, brokerid=brokerid)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        incpos = INCPOS(dtasof=dtasof, include=incpos)
        stmtrq = INVSTMTRQ(invacctfrom=acct, inctran=inctran, incoo=incoo,
                           incpos=incpos, incbal=incbal)
        trnuid = uuid.uuid4()
        return INVSTMTTRNRQ(trnuid=trnuid, invstmtrq=stmtrq)

    def download(self, ofx):
        """ """
        # py3k: ElementTree.tostring() returns bytes not str
        data = self.ofxheader + ET.tostring(ofx.to_etree()).decode()

        mimetype = 'application/x-ofx'
        headers = {'Content-type': mimetype, 'Accept': '*/*, %s' % mimetype}

        try:
            response = requests.post(self.url, data=data, headers=headers)
            return StringIO(response.text)
        except requests.HTTPError as err:
            # FIXME
            print(err.info())
            raise


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
