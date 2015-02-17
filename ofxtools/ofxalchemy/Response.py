# vim: set fileencoding=utf-8
""" 
Python object model for Aggregate containers (the OFX response, statements,
transaction lists, etc.)
"""

# local imports
import models
from models import DBSession, Aggregate, INVPOS 
import types

class OFXResponse(object):
    """ 
    Top-level object representing an OFX response converted into Python
    data types, with attributes for convenient access to statements (i.e.
    OFX *STMT aggregates), security descriptions (i.e. OFX SECLIST aggregate),
    and SONRS (server response to signon request).

    After conversion, each of these convenience attributes holds instances
    of various Aggregate subclasses.
    """
    statements = []
    securities = []

    def __init__(self, tree, strict=True):
        """ 
        Initialize with ofx.ElementTree instance containing parsed OFX.

        The strict argument determines whether to throw an error for certain
        OFX data validation violations.
        """
        # Keep a reference to the parse tree
        self.tree = tree

        # SECLIST - list of description of securities referenced by
        # INVSTMT (investment account statement)
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is not None:
            # We need to instantiate on the SECINFO subclass (not Aggregate)
            # b/c handling MFINFO *ASSETCLASS lists requires overriding
            # Aggregate.from_etree()
            self.securities = [
                getattr(models, sec.tag).from_etree(sec, get_or_create=True) \
                for sec in seclist
            ]
            DBSession.add_all(self.securities)
            DBSession.commit()

        # TRNRS - transaction response, which is the main section
        # containing account statements
        #
        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        for stmtClass in (BankStatement, CreditCardStatement, InvestmentStatement):
            tagname = stmtClass._tagName
            for trnrs in self.tree.findall('*/%sTRNRS' % tagname):
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                stmtrs = trnrs.find('%sRS' % tagname)
                if stmtrs is not None:
                    stmt = stmtClass(stmtrs)
                    self.statements.append(stmt)

    def __repr__(self):
        s = "<%s len(statements)=%d len(securities)=%d>"
        return s % (self.__class__.__name__, 
                    len(self.statements), 
                    len(self.securities),
                   )

### STATEMENTS
class Statement(object):
    """ Base class for Python representation of OFX *STMT aggregate """
    currency = None
    account = None

    transactions = []
    other_balances =[] 

    def __init__(self, stmtrs):
        """ Initialize with *STMTRS Element """
        self.currency = stmtrs.find('CURDEF').text
        acctfrom = stmtrs.find(self._acctTag)
        self.account = Aggregate.from_etree(acctfrom, get_or_create=True)
        DBSession.add(self.account)
        DBSession.commit()
        self._init(stmtrs)

    def _init(self, stmtrs):
        # Define in subclass
        raise NotImplementedError
    
    def from_etree(elem):
        # Define in subclass
        raise NotImplementedError

    def __repr__(self):
        # Define in subclass
        raise NotImplementedError


class BankStatement(Statement):
    """ Python representation of OFX STMT (bank statement) aggregate """
    ledgerbal = None
    availbal = None

    _tagName = 'STMT'
    _acctTag = 'BANKACCTFROM'

    def _init(self, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            self.transactions = BANKTRANLIST(self.account, tranlist)
            DBSession.add_all(self.transactions)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        self.ledgerbal = Aggregate.from_etree(
            ledgerbal, acctfrom_id=self.account.id, get_or_create=True
        )
        DBSession.add(self.ledgerbal)

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            self.availbal = Aggregate.from_etree(
                availbal, acctfrom_id=self.account.id, get_or_create=True
            )
            DBSession.add(self.availbal)

        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.other_balances = [Aggregate.from_etree(bal) for bal in ballist]
            DBSession.add_all(self.other_balances)

        # Unsupported subaggregates
        for tag in ('MKTGINFO', ):
            child = stmtrs.find(tag)
            if child:
                stmtrs.remove

    def __repr__(self):
        s = "<%s account=%s currency=%s ledgerbal=%s availbal=%s len(other_balances)=%d len(transactions)=%d>"
        return s % (self.__class__.__name__, 
                    self.account,
                    self.currency,
                    self.ledgerbal, 
                    self.availbal, 
                    len(self.other_balances),
                    len(self.transactions), 
                   )


class CreditCardStatement(BankStatement):
    """ 
    Python representation of OFX CCSTMT (credit card statement) 
    aggregate 
    """
    _tagName = 'CCSTMT'
    _acctTag = 'CCACCTFROM'


class InvestmentStatement(Statement):
    """ 
    Python representation of OFX InvestmentStatement (investment account statement) 
    aggregate 
    """
    datetime = None

    positions = []
    balances = []

    _tagName = 'INVSTMT'
    _acctTag = 'INVACCTFROM'

    def _init(self, invstmtrs):
        dtasof = invstmtrs.find('DTASOF').text
        self.datetime = types.OFXDateTimeConverter.convert(dtasof)

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            self.transactions = INVTRANLIST(self.account, tranlist)
            DBSession.add_all(self.transactions)

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            self.positions = [Aggregate.from_etree(
                pos, acctfrom_id=self.account.id, dtasof=self.datetime,
                get_or_create=True) for pos in poslist]
            DBSession.add_all(self.positions)

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal is not None:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist is not None:
                invbal.remove(ballist)
                self.other_balances = [
                    Aggregate.from_etree(
                        bal, acctfrom_id=self.account.id, dtasof=self.datetime,
                        get_or_create=True
                    ) for bal in ballist
                ]
                DBSession.add_all(self.other_balances)
            # Now we can flatten the rest of INVBAL
            self.balances = Aggregate.from_etree(
                invbal, acctfrom_id=self.account.id, dtasof=self.datetime,
                get_or_create=True
            )
            DBSession.add(self.balances)

        # Unsupported subaggregates
        for tag in ('INVOOLIST', 'INV401K', 'INV401KBAL', 'MKTGINFO'):
            child = invstmtrs.find(tag)
            if child is not None:
                invstmtrs.remove

    def __repr__(self):
        s = """
            <%s datetime='%s' account=%s currency='%s' balances=%s 
            \len(other_balances)=%d len(positions)=%d len(transactions)=%d>
        """
        return s % (self.__class__.__name__, 
                    self.datetime,
                    self.account,
                    self.currency,
                    self.balances, 
                    len(self.other_balances),
                    len(self.positions), 
                    len(self.transactions), 
                   )


### TRANSACTION LISTS
class TransactionList(list):
    """ 
    Base class for Python representation of OFX *TRANLIST (transaction list) 
    aggregate 
    """
    def __init__(self, account, tranlist):
        self.account = account
        dtstart, dtend = tranlist[0:2]
        tranlist = tranlist[2:]
        self.dtstart = types.OFXDateTimeConverter.convert(dtstart.text)
        self.dtend = types.OFXDateTimeConverter.convert(dtend.text)
        self.extend([self.etree_to_sql(tran) for tran in tranlist])

    def etree_to_sql(self, tran):
        instance = Aggregate.from_etree(tran, acctfrom_id=self.account.id,
                                        get_or_create=True)
        return instance

    def __repr__(self):
        return "<%s dtstart='%s' dtend='%s' len(self)=%d>" % \
                (self.__class__.__name__, self.dtstart, self.dtend, len(self))


class BANKTRANLIST(TransactionList):
    """
    Python representation of OFX BANKTRANLIST (bank transaction list) 
    aggregate
    """
    pass


class INVTRANLIST(TransactionList):
    """
    Python representation of OFX INVTRANLIST (investment transaction list)
    aggregate 
    """
    pass

