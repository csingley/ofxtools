#!/usr/bin/env python
# vim: set fileencoding=utf-8
"""
Network client that composes/transmits Open Financial Exchange (OFX) requests,
and receives OFX responses in reply.  A basic CLI utility is included.

To use, create an OFXClient instance configured with OFX connection parameters:
server URL, OFX protocol version, financial institution identifiers, client
identifiers, etc.

If you don't have these, try http://ofxhome.com/ .

Using the configured OFXClient instance, make a request by calling the
relevant method, e.g. `OFXClient.request_statements()`.  OFX supports
multi-part statement requests, so `request_statements` accepts sequences as
arguments.  Simple data containers for each statement
(`StmtRq`, `CcStmtRq`, etc.) are provided.

The method call therefore looks like this:

>>> client = OFXClient('https://onlinebanking.capitalone.com/ofx/process.ofx',
...                    org='Hibernia', fid='1001', bankid='056073502',
...                    appver=202)
>>> s0 = StmtRq(acctid='1', accttype='CHECKING',
...             dtstart=datetime.date(2015, 1, 1),
...             dtend=datetime.date(2015, 1, 31))
>>> s1 = StmtRq(acctid='2', accttype='SAVINGS',
...             dtstart=datetime.date(2015, 1, 1),
...             dtend=datetime.date(2015, 1, 31))
>>> c0 = CcStmtRq(acctid='3',
...               dtstart=datetime.date(2015, 1, 1),
...               dtend=datetime.date(2015, 1, 31))
>>> response = client.request_statements(user='jpmorgan', password='t0ps3kr1t',
...                                      stmtrqs=[s0, s1], ccstmtrqs=[c0])
"""

# stdlib imports
import datetime
import uuid
import xml.etree.ElementTree as ET
from collections import (namedtuple, defaultdict,)
from os import path
from getpass import getpass

from ofxtools.models import ACCTINFORQ, ACCTINFOTRNRQ, SIGNUPMSGSRQV1

from configparser import SafeConfigParser
from urllib.parse import urlparse
from io import BytesIO

# 3rd party imports
import requests


# local imports
from ofxtools.header import make_header
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
    CCSTMTENDTRNRQ, CCSTMTENDRQ)
from ofxtools.models.investment import (
    INVSTMTMSGSRQV1, INVSTMTTRNRQ, INVSTMTRQ, INVACCTFROM, INCPOS,
)
from ofxtools.Types import DateTime
from ofxtools.utils import (fixpath, UTC)


# Statement request data containers
# Pass sequences of these containers as args to OFXClient.request_statement()
StmtRq = namedtuple('StmtRq', ['acctid', 'accttype', 'dtstart', 'dtend',
                               'inctran'])
StmtRq.__new__.__defaults__ = (None, None, None, None, True)

CcStmtRq = namedtuple('CcStmtRq', ['acctid', 'dtstart', 'dtend', 'inctran'])
CcStmtRq.__new__.__defaults__ = (None, None, None, True)

CcStmtEndRq = namedtuple('CcStmtRq', ['acctid', 'dtstart', 'dtend', 'incstmtimg'])
CcStmtEndRq.__new__.__defaults__ = (None, None, None, False)

InvStmtRq = namedtuple('InvStmtRq', ['acctid', 'dtstart', 'dtend', 'dtasof',
                                     'inctran', 'incoo', 'incpos', 'incbal'])
InvStmtRq.__new__.__defaults__ = (None, None, None, None, True, False, True,
                                  True)


class OFXClient:
    """
    Basic OFX client to download statement and profile requests.
    """
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
        return str(make_header(version=self.version, newfileuid=uuid.uuid4()))

    def request_statements(self, user, password, clientuid=None,
                           stmtrqs=None, ccstmtrqs=None, invstmtrqs=None,
                           dryrun=False, prettyprint=None,
                           close_elements=True):
        """
        Package and send OFX statement requests (STMTRQ/CCSTMTRQ/INVSTMTRQ).

        Input *rqs are sequences of the corresponding namedtuples
        (StmtRq, CcStmtRq, InvStmtRq)
        """
        signonmsgs = self.signon(user, password, clientuid=clientuid)

        bankmsgs = None
        if stmtrqs:
            # bankid comes from OFXClient instance attribute,
            # not StmtRq namedtuple
            stmttrnrqs = [self.stmttrnrq(
                **dict(stmtrq._asdict(), bankid=self.bankid))
                for stmtrq in stmtrqs]
            bankmsgs = BANKMSGSRQV1(*stmttrnrqs)

        creditcardmsgs = None
        if ccstmtrqs:
            ccstmttrnrqs = [self.ccstmttrnrq(**stmtrq._asdict())
                            for stmtrq in ccstmtrqs]
            creditcardmsgs = CREDITCARDMSGSRQV1(*ccstmttrnrqs)

        invstmtmsgs = None
        if invstmtrqs:
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
        return self.download(ofx, dryrun=dryrun, prettyprint=prettyprint,
                             close_elements=close_elements)

    def request_end_statements(self, user, password, clientuid=None,
                               ccstmendtrqs=None,
                               dryrun=False, prettyprint=None):
        """
        Package and send OFX end statement requests (CCSTMTENDRQ).

        Input *rqs are sequences of the corresponding namedtuples CcStmtEndRq
        """
        signonmsgs = self.signon(user, password, clientuid=clientuid)

        # TODO: Support Bank and Investments.
        creditcardmsgs = None
        if ccstmendtrqs:
            ccstmtendtrnrqs = [self.ccstmtendtrnrq(**stmtendrq._asdict())
                               for stmtendrq in ccstmendtrqs]
            creditcardmsgs = CREDITCARDMSGSRQV1(*ccstmtendtrnrqs)

        ofx = OFX(signonmsgsrqv1=signonmsgs,
                  creditcardmsgsrqv1=creditcardmsgs)
        return self.download(ofx, dryrun=dryrun, prettyprint=prettyprint)

    def request_profile(self, user=None, password=None, dryrun=False,
                        prettyprint=None, close_elements=True):
        """
        Package and send OFX profile requests (PROFRQ).
        """

        dtprofup = datetime.datetime(1990, 1, 1, tzinfo=UTC)
        profrq = PROFRQ(clientrouting='NONE', dtprofup=dtprofup)
        trnuid = uuid.uuid4()
        proftrnrq = PROFTRNRQ(trnuid=trnuid, profrq=profrq)
        msgs = PROFMSGSRQV1(proftrnrq)

        user = user or '{:0<32}'.format('anonymous')
        password = password or '{:0<32}'.format('anonymous')
        signonmsgs = self.signon(user, password)

        ofx = OFX(signonmsgsrqv1=signonmsgs, profmsgsrqv1=msgs)
        return self.download(ofx, dryrun=dryrun, prettyprint=prettyprint,
                             close_elements=close_elements)

    def request_accounts(self, user, password, dtacctup, clientuid=None,
                         dryrun=False, prettyprint=None, close_elements=True):
        """
        Package and send OFX account info requests (ACCTINFORQ)
        """
        signonmsgs = self.signon(user, password, clientuid=clientuid)
        acctinforq = ACCTINFORQ(dtacctup=dtacctup)
        acctinfotrnrq = ACCTINFOTRNRQ(trnuid=uuid.uuid4(),
                                      acctinforq=acctinforq)
        signupmsgs = SIGNUPMSGSRQV1(acctinfotrnrq)

        ofx = OFX(signonmsgsrqv1=signonmsgs,
                  signupmsgsrqv1=signupmsgs)
        return self.download(ofx, dryrun=dryrun, prettyprint=prettyprint,
                             close_elements=close_elements)

    def signon(self, userid, userpass, sesscookie=None, clientuid=None):
        """ Construct SONRQ; package in SIGNONMSGSRQV1 """
        if self.org:
            fi = FI(org=self.org, fid=self.fid)
        else:
            fi = None

        dtclient = datetime.datetime.now(UTC)
        sonrq = SONRQ(dtclient=dtclient, userid=userid, userpass=userpass,
                      language=self.language, fi=fi, sesscookie=sesscookie,
                      appid=self.appid, appver=self.appver,
                      clientuid=clientuid)
        return SIGNONMSGSRQV1(sonrq=sonrq)

    def stmttrnrq(self, bankid, acctid, accttype, dtstart=None, dtend=None,
                  inctran=True):
        """ Construct STMTRQ; package in STMTTRNRQ """
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = STMTRQ(bankacctfrom=acct, inctran=inctran)
        trnuid = uuid.uuid4()
        return STMTTRNRQ(trnuid=trnuid, stmtrq=stmtrq)

    def ccstmttrnrq(self, acctid, dtstart=None, dtend=None, inctran=True):
        """ Construct CCSTMTRQ; package in CCSTMTTRNRQ """
        acct = CCACCTFROM(acctid=acctid)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = CCSTMTRQ(ccacctfrom=acct, inctran=inctran)
        trnuid = uuid.uuid4()
        return CCSTMTTRNRQ(trnuid=trnuid, ccstmtrq=stmtrq)

    def ccstmtendtrnrq(self, acctid, dtstart=None, dtend=None, incstmtimg=False):
        """ Construct CCSTMTENDRQ; package in CCSTMTENDTRNRQ """
        acct = CCACCTFROM(acctid=acctid)
        stmtrq = CCSTMTENDRQ(ccacctfrom=acct, dtstart=dtstart, dtend=dtend,
                             incstmtimg=incstmtimg)
        trnuid = uuid.uuid4()
        return CCSTMTENDTRNRQ(trnuid=trnuid, ccstmtendrq=stmtrq)

    def invstmttrnrq(self, acctid, brokerid,
                     dtstart=None, dtend=None, inctran=True, incoo=False,
                     dtasof=None, incpos=True, incbal=True):
        """ Construct INVSTMTRQ; package in INVSTMTTRNRQ """
        acct = INVACCTFROM(acctid=acctid, brokerid=brokerid)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        incpos = INCPOS(dtasof=dtasof, include=incpos)
        stmtrq = INVSTMTRQ(invacctfrom=acct, inctran=inctran, incoo=incoo,
                           incpos=incpos, incbal=incbal)
        trnuid = uuid.uuid4()
        return INVSTMTTRNRQ(trnuid=trnuid, invstmtrq=stmtrq)

    def download(self, ofx, dryrun=False, prettyprint=None,
                 close_elements=True):
        """ Package complete OFX tree and POST to server """
        tree = ofx.to_etree()

        if prettyprint is None:
            prettyprint = True

        if prettyprint:
            indent(tree)

        # Some servers choke on OFXv1 requests including ending tags for
        # elements (which are optional per the spec).
        if close_elements is False:
            if self.version >= 200:
                msg = 'OFX version {} requires ending tags for elements'
                raise ValueError(msg)
            body = tostring_unclosed_elements(tree)
        else:
            body = ET.tostring(tree).decode()

        data = self.ofxheader + body

        if dryrun:
            return BytesIO(data.encode("ascii"))

        mimetype = 'application/x-ofx'
        # requests.utils.default_headers() sets
        # {'User-Agent': 'python-requests/{}'.format(requests.__version)
        # which apparently displeases some FIs
        headers = {'User-Agent': None, 'Content-type': mimetype,
                   'Accept': '*/*, %s' % mimetype}

        try:
            response = requests.post(self.url, data=data, headers=headers)
            return BytesIO(response.content)
        except requests.HTTPError as err:
            # FIXME
            print(err.info())
            raise


### UTILITIES
def indent(elem, level=0):
    """
    Indent Element.text by nesting level.

    http://effbot.org/zone/element-lib.htm#prettyprint
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def tostring_unclosed_elements(node):
    if len(node) == 0:
        output = '<{}>{}\n'.format(node.tag, node.text)
    else:
        output = '<{}>\n'.format(node.tag)
        for child in node:
            output += tostring_unclosed_elements(child)
        output += '</{}>\n'.format(node.tag)
    return output


### CLI COMMANDS
def init_client(args):
    """
    Initialize OFXClient with connection info from args
    """
    client = OFXClient(args.url, org=args.org, fid=args.fid,
                       version=args.version, appid=args.appid,
                       appver=args.appver, language=args.language,
                       bankid=args.bankid, brokerid=args.brokerid)
    return client


def do_stmt(args):
    """
    Construct OFX statement request from CLI/config args; send to server.

    Returns a file-like object (BytesIO) that can be passed to
    OFXTree.parse()
    """
    client = init_client(args)

    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(getattr(args, d)) for d in ('dtstart', 'dtend', 'dtasof')}

    # Define statement requests
    stmtrqs = defaultdict(list)
    for accttype in ('checking', 'savings', 'moneymrkt', 'creditline'):
        acctids = getattr(args, accttype, [])
        stmtrqs['stmtrqs'].extend(
            [StmtRq(acctid=acctid, accttype=accttype.upper(),
                    dtstart=dt['start'], dtend=dt['end'], inctran=args.inctran)
             for acctid in acctids])

    for acctid in args.creditcard:
        stmtrqs['ccstmtrqs'].append(
            CcStmtRq(acctid=acctid, dtstart=dt['start'], dtend=dt['end'],
                     inctran=args.inctran))

    for acctid in args.investment:
        stmtrqs['invstmtrqs'].append(
            InvStmtRq(acctid=acctid, dtstart=dt['start'], dtend=dt['end'],
                      dtasof=dt['asof'], inctran=args.inctran,
                      incoo=args.incoo, incpos=args.incpos,
                      incbal=args.incbal))

    # Use dummy password for dummy request
    if args.dryrun:
        password = '{:0<32}'.format('anonymous')
    else:
        password = getpass()

    response = client.request_statements(
        args.user, password, clientuid=args.clientuid, dryrun=args.dryrun,
        close_elements=not args.unclosedelements, **stmtrqs).read()

    if hasattr(response, 'decode'):
        response = response.decode()
    print(response)


def do_profile(args):
    """
    Construct OFX profile request from CLI/config args; send to server.

    Returns a file-like object (BytesIO) that can be passed to
    OFXTree.parse()
    """
    client = init_client(args)
    response = client.request_profile(dryrun=args.dryrun,
                                      close_elements=not args.unclosedelements)
    print(response.read())


class OFXConfigParser(SafeConfigParser):
    """
    INI parser that loads default FI configs from oftools/config/fi.cfg and
    updates them from the user config file specified in its [global] section.

    It also provides a list of configured FIs (i.e. config sections except
    for [global]) for use by the CLI --help.
    """
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
        """ List of configured FIs """
        sections = self.sections()
        sections.remove('global')
        return sections


def main():
    """
    Merge default FI configs with user configs from oftools.cfg and
    CLI args, then pass to do_stmt() or do_profile()
    """
    # Read config first, so fi_index can be used in help
    config = OFXConfigParser()
    config.read()

    from argparse import ArgumentParser

    argparser = ArgumentParser(description='Download OFX financial data',
                               epilog='FIs configured: %s' % config.fi_index)
    argparser.add_argument('server',
                           help='OFX server - URL or FI name from config')
    argparser.add_argument('-n', '--dryrun', action='store_true',
                           default=False, help='display OFX request and exit')
    argparser.add_argument('-p', '--profile', action='store_true',
                           default=False,
                           help='Download OFX profile instead of statement')
    argparser.add_argument('--unclosedelements', action='store_true',
                           default=False,
                           help='Omit end tags for elements (OFXv1 only)')

    signon_group = argparser.add_argument_group(title='Signon Options')
    signon_group.add_argument('-u', '--user', help='FI login username')
    signon_group.add_argument('--clientuid', help='OFX client UID')
    signon_group.add_argument('--org', help='FI.ORG')
    signon_group.add_argument('--fid', help='FI.FID')
    signon_group.add_argument('--bankid', help='ABA routing#')
    signon_group.add_argument('--brokerid', help='Broker ID string')
    signon_group.add_argument('--version', help='OFX version')
    signon_group.add_argument('--appid', help='OFX client app identifier')
    signon_group.add_argument('--appver', help='OFX client app version')
    signon_group.add_argument('--language', default='ENG', help='OFX language')

    acct_group = argparser.add_argument_group(title='Account Options')
    acct_group.add_argument('-C', '--checking', metavar='acct#',
                            action='append', default=[])
    acct_group.add_argument('-S', '--savings', metavar='acct#',
                            action='append', default=[])
    acct_group.add_argument('-M', '--moneymrkt', metavar='acct#',
                            action='append', default=[])
    acct_group.add_argument('-L', '--creditline', metavar='acct#',
                            action='append', default=[])
    acct_group.add_argument('-c', '--creditcard', '--cc', metavar='acct#',
                            action='append', default=[])
    acct_group.add_argument('-i', '--investment', metavar='acct#',
                            action='append', default=[])

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
    stmt_group.add_argument('--open-orders', dest='incoo',
                            action='store_true', default=False,
                            help='Include open orders')

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
    if args.profile:
        do_profile(args)
    else:
        do_stmt(args)


if __name__ == '__main__':
    main()
