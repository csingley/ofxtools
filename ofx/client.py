import urllib2
import datetime
import uuid
from xml.etree.cElementTree import Element, SubElement, tostring

import valid

dtConverter = valid.OFXDtConverter()
stringBool = valid.OFXStringBool()
accttypeValidator = valid.validators.OneOf(valid.ACCOUNT_TYPES)

class OFXClient(object):
    """ """
    #appid = 'Money' # Masquerade as MS Money
    #appver = '1700' # 1500=Money 2006, 1600=Money 2007, 1700=Money Plus
    appid = 'QWIN' # Masquerade as Quicken for Windows
    appver = '1700' # 1500=Quicken 2006, 1600=Quicken 2007, 1700=Quicken 2008

    def __init__(self, url, fiorg=None, fid=None, bankid=None, brokerid=None,
    version=102):
        # Initialize
        self.reset()

        self.url = url
        self.fiorg = fiorg
        self.fid = fid
        self.bankid = bankid
        self.brokerid = brokerid
        self.version = version

    def reset(self):
        self.signon = None
        self.bank = None
        self.creditcard = None
        self.investment = None
        self.request = None
        self.response = None

    def download(self):
        mime = 'application/x-ofx'
        headers = {'Content-type': mime, 'Accept': '*/*, %s' % mime}
        if not self.request:
            self.do_request() # FIXME
        http = urllib2.Request(self.url, self.request, headers)
        self.response = urllib2.urlopen(http)
        return self.response

    def do_request(self):
        ofx = Element('OFX')
        if not self.signon:
            raise ValueError # FIXME
        ofx.append(self.signon)
        for msgset in ('bank', 'creditcard', 'investment'):
            msgset = getattr(self, msgset, None)
            if msgset:
                ofx.append(msgset)
        self.request = self.header + tostring(ofx)
        return self.request

    def do_signon(self, user, password):
        msgsrq = Element('SIGNONMSGSRQV1')
        sonrq = SubElement(msgsrq, 'SONRQ')
        SubElement(sonrq, 'DTCLIENT').text = dtConverter.from_python(datetime.datetime.now())
        SubElement(sonrq, 'USERID').text = user
        SubElement(sonrq, 'USERPASS').text = password
        SubElement(sonrq, 'LANGUAGE').text = 'ENG'
        if self.fiorg:
            fi = SubElement(sonrq, 'FI')
            SubElement(fi, 'ORG').text = self.fiorg
            if self.fid:
                SubElement(fi, 'FID').text = self.fid
        SubElement(sonrq, 'APPID').text = self.appid
        SubElement(sonrq, 'APPVER').text = self.appver
        self.signon = msgsrq

    def do_bank(self, accounts, include_transactions=True, dtstart=None, dtend=None):
        """
        Requesting transactions without dtstart/dtend (which is the default)
        asks for all transactions on record.
        """
        msgsrq = Element('BANKMSGSRQV1')
        for account in accounts:
            try:
                accttype, acctid = account
                accttype = accttypeValidator.to_python(accttype)
            except ValueError:
                raise ValueError('Accounts must be a sequence of (ACCTTYPE, ACCTID) pairs')
            stmtrq = self.wrap_request(msgsrq, 'STMTRQ')
            acctfrom = SubElement(stmtrq, 'BANKACCTFROM')
            SubElement(acctfrom, 'BANKID').text = self.bankid
            SubElement(acctfrom, 'ACCTID').text = acctid
            SubElement(acctfrom, 'ACCTTYPE').text = accttype

            self.include_transactions(stmtrq, include_transactions, dtstart, dtend)
        self.bank = msgsrq

    def do_creditcard(self, accounts, include_transactions=True, dtstart=None, dtend=None):
        """
        Requesting transactions without dtstart/dtend (which is the default)
        asks for all transactions on record.
        """
        msgsrq = Element('CREDITCARDMSGSRQV1')
        for account in accounts:
            stmtrq = self.wrap_request(msgsrq, 'CCSTMTRQ')
            acctfrom = SubElement(stmtrq, 'CCACCTFROM')
            SubElement(acctfrom, 'ACCTID').text = account

            self.include_transactions(stmtrq, include_transactions, dtstart, dtend)
        self.creditcard = msgsrq

    def do_investment(self, accounts,
                    include_transactions=True, dtstart=None, dtend=None,
                    include_positions=True, dtasof=None,
                    include_balances=True):
        """ """
        msgsrq = Element('INVSTMTMSGSRQV1')
        for account in accounts:
            stmtrq = self.wrap_request(msgsrq, 'INVSTMTRQ')
            acctfrom = SubElement(stmtrq, 'INVACCTFROM')
            SubElement(acctfrom, 'BROKERID').text = self.brokerid
            SubElement(acctfrom, 'ACCTID').text = account

            self.include_transactions(stmtrq, include_transactions, dtstart, dtend)

            SubElement(stmtrq, 'INCOO').text = 'N'

            incpos = SubElement(stmtrq, 'INCPOS')
            if dtasof:
                SubElement(incpos, 'DTASOF').text = dtConverter.from_python(dtasof)
            SubElement(incpos, 'INCLUDE').text = stringBool.from_python(include_positions)

            SubElement(stmtrq, 'INCBAL').text = stringBool.from_python(include_balances)
        self.investment = msgsrq

    # Utilities
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
            raise ValueError # FIXME

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

clients = {'ameritrade': OFXClient(url='https://ofxs.ameritrade.com/cgi-bin/apps/OFX',
                        fiorg='Ameritrade Technology Group',
                        fid='AIS', brokerid='ameritrade.com'),
                'etrade': OFXClient(url='https://ofx.etrade.com/cgi-ofx/etradeofx',
                        fid='9989', brokerid='etrade.com'),
                'compass': OFXClient(url='https://www2.compassweb.com/ofxsecurity/ofx_security_server.dll',
                        fiorg='CompassBank',
                        fid='2201', bankid='113010547'),
                'chase': OFXClient(url='https://ofx.chase.com',
                        fiorg='B1', fid='10898'),
                'ibc': OFXClient(url='https://ibcbankonline2.ibc.com/scripts/serverext.dll',
                        fiorg='IBC', fid='1001', bankid='113000861'),
                'capitalone': OFXClient(url='https://onlinebanking.capitalone.com/ofx/process.ofx',
                        fiorg='Hibernia', fid='1001', bankid='111915709'),
}

def main():
    from optparse import OptionParser, OptionGroup
    import getpass

    usage = "usage: %prog [options] institution (bank | creditcard | investment) account [account account ...]"
    optparser = OptionParser(usage=usage)
    optparser.set_defaults(accttype='CHECKING',
                            inctran=True, dtstart=None, dtend=None,
                            incpos=True, dtasof=None, incbal=True)
    optparser.add_option('-l', '--list', action='store_true',
                        help='list known institutions and exit')
    optparser.add_option('-u', '--user', help='login user ID at institution')
    # account options
    acctgroup = OptionGroup(optparser, 'Bank Account Options')
    acctgroup.add_option('-c', '--checking', action='store_const',
                        const='CHECKING', dest='accttype',
                        help='specify checking account type')
    acctgroup.add_option('-a', '--savings', action='store_const',
                        const='SAVINGS', dest='accttype',
                        help='specify checking account type')
    acctgroup.add_option('-m', '--moneymrkt', action='store_const',
                        const='MONEYMRKT', dest='accttype',
                        help='specify money market account type')
    acctgroup.add_option('-r', '--creditline', action='store_const',
                        const='CREDITLINE', dest='accttype',
                        help='specify credit line account type')
    optparser.add_option_group(acctgroup)
    # Transaction options
    transgroup = OptionGroup(optparser, 'Transaction-Related Options')
    transgroup.add_option('-t', '--skip-transactions', dest='inctran',
                        action='store_false', help='omit transaction data')
    transgroup.add_option('-s', '--start', dest='dtstart', help='start of date range')
    transgroup.add_option('-e', '--end', dest='dtend', help='end of date range')
    optparser.add_option_group(transgroup)
    # Position options
    posgroup = OptionGroup(optparser, '(Investment) Position-Related Options')
    posgroup.add_option('-p', '--skip-positions', dest='incpos',
                        action='store_false', help='omit position data')
    posgroup.add_option('-d', '--date', dest='dtasof', help='as-of date')
    optparser.add_option_group(posgroup)
    # Balance options
    balgroup = OptionGroup(optparser, '(Investment) Balance-Related Options')
    balgroup.add_option('-b', '--skip-balances', dest='incbal',
                        action='store_false', help='omit balance data')
    optparser.add_option_group(balgroup)

    # Process
    (options, args) = optparser.parse_args()

    if options.list:
        print clients.keys()
        return

    if not args:
        optparser.print_usage()
        return

    fi = args.pop(0)
    try:
        client = clients[fi]
    except KeyError:
        raise ValueError("unknown institution '%s'" % fi) # FIXME

    # Dispatch method to write message request
    fitype = args.pop(0)
    try:
        write_request = getattr(client, 'do_%s' % fitype)
    except AttributeError:
        raise ValueError("unknown institution type '%s'" % fitype) # FIXME

    # Convert dtXXX str -> datetime.date
    dateconv = valid.validators.DateConverter(if_empty=None)
    for attr in ('dtstart', 'dtend', 'dtasof'):
        dt = getattr(options, attr, None)
        setattr(options, attr, dateconv.to_python(dt))

    # Construct arguments for message request
    request_args = {'accounts': args, 'include_transactions': options.inctran,
                    'dtstart': options.dtstart, 'dtend': options.dtend,
    }
    if fitype == 'bank':
        accts = request_args['accounts']
        request_args['accounts'] = [(options.accttype, acct) for acct in accts]
    if fitype == 'investment':
        request_args.update({'include_positions': options.incpos,
                            'dtasof': options.dtasof,
                            'include_balances': options.incbal,
                            }
        )

    # Execute method to write message request
    write_request(**request_args)

    if options.user:
        passwd = getpass.getpass()
        client.do_signon(options.user, passwd)
    else:
        # FIXME
        raise ValueError("Need username/password to authenticate download")

    #print client.do_request()
    #return

    try:
        response = client.download()
    except urllib2.HTTPError as err:
        raise
    print response.read()

if __name__ == '__main__':
    main()