# vim: set fileencoding=utf-8
"""
Version of ofxtools.Parser that uses SQLAlchemy for conversion
"""
# stdlib imports
from decimal import Decimal


# 3rd party imports
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from sqlalchemy.orm.exc import NoResultFound


# local imports
import ofxtools
from ofxtools.Parser import SubElement
from ofxtools.ofxalchemy import models


class Element(ofxtools.Parser.Element):
    """ """
    attributes = {}
    extra_attributes = {}

    def _dereference(self, DBSession):
        """ """
        reference = self.instantiate(DBSession)
        self.clear()
        return reference

    def _do_origcurrency(self):
        """
        See OFX spec section 5.2 for currency handling conventions.
        Flattening the currency definition leaves only the CURRATE/CURSYM
        elements, leaving no indication of whether these were sourced from
        a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        important to interpreting transactions in foreign correncies, we
        preserve this information by adding a nonstandard curtype element.
        """
        currency = self.find('*/CURRENCY')
        origcurrency = self.find('*/ORIGCURRENCY')
        if (currency is not None) or (origcurrency is not None):
            if (currency is not None) and (origcurrency is not None):
                msg = '<%s> may not contain both <CURRENCY> and <ORIGCURRENCY>' % elem.tag
                raise ofxtools.Parser.ParseError(msg)
            curtype = currency
            if curtype is None:
                curtype = origcurrency
            if (curtype is not None):
                extra_attributes = self.get('extra_attributes')
                extra_attributes['curtype'] = curtype.tag
                self.set('extra_attributes', extra_attributes)

    def _preflatten(self, DBSession):
        """ """
        if self.tag == 'OPTINFO':
            # A <SECID> aggregate referring to the security underlying the
            # option is, in general, *not* going to be contained in <SECLIST>
            # (because you don't necessarily have a position in the underlying).
            # Since the <SECID> for the underlying only gives us fields for
            # (uniqueidtype, uniqueid) we can't really go ahead and use this
            # information to create a corresponding SECINFO instance (since we
            # lack information about the security subclass).  It's unclear that
            # the SECID of the underlying is really needed for anything, so we
            # disregard it.
            secid = self.find('./SECID')
            if secid is not None:
                self.remove(secid)

        elif self.tag == 'MFINFO':
            # Strip {MF, FIMF}ASSETCLASS - lists that will blow up _flatten()
            # These are nearly useless for asset allocation since they're
            # so unreliable.  Since they're also a lot of trouble to process,
            # we're just going to delete them.
            #
            # Do all XPath searches before removing nodes from the tree
            #   which seems to mess up the DOM in Python3 and throw an
            #   AttributeError on subsequent searches.
            mfassetclass = self.find('./MFASSETCLASS')
            fimfassetclass = self.find('./FIMFASSETCLASS')

            if mfassetclass is not None:
                self.remove(mfassetclass)
            if fimfassetclass is not None:
                self.remove(fimfassetclass)

        elif self.tag.startswith('POS'):
            secid = self.find('.//SECID')
            if secid is None:
                msg = '<%s> does not contain <SECID>'
                raise ofxtools.Parser.ParseError(msg)
            extra_attributes = self.get('extra_attributes')
            extra_attributes['secinfo'] = secid._dereference(DBSession)
            self.set('extra_attributes', extra_attributes)

        elif self.tag in ('STMTTRN', 'INVBANKTRAN'):
            # Replace BANKACCTTO/CCACCTTO/PAYEE with FK references.  This is
            # needed for {BANK,CC}ACCTTO because account type information is
            # contained in the aggregate container, which will be lost by
            # _flatten().  PAYEE will not lose information when _flatten()ed,
            # but it really needs its own object class to be useful.
            #
            # Do all XPath searches before removing nodes from the tree
            #   which seems to mess up the DOM in Python3 and throw an
            #   AttributeError on subsequent searches.
            bankacctto = self.find('BANKACCTTO')
            ccacctto = self.find('CCACCTTO')
            payee = self.find('PAYEE')

            self._do_origcurrency()

            if bankacctto is not None:
                extra_attributes = self.get('extra_attributes')
                extra_attributes['acctto'] = bankacctto._dereference(DBSession)
                self.set('extra_attributes', extra_attributes)
            if ccacctto is not None:
                extra_attributes = self.get('extra_attributes')
                extra_attributes['acctto'] = ccacctto._dereference(DBSession)
                self.set('extra_attributes', extra_attributes)
            if (bankacctto is not None) and (ccacctto is not None):
                msg = '<%s> may not contain both <BANKACCTTO> and <CCACCTTO>' % self.tag
                raise ofxtools.Parser.ParseError(msg)
            if payee is not None:
                extra_attributes = self.get('extra_attributes')
                extra_attributes['payee'] = payee._dereference(DBSession)
                self.set('extra_attributes', extra_attributes)

        elif self.find('.//INVTRAN') is not None:
            # Do all XPath searches before removing nodes from the tree
            #   which seems to mess up the DOM in Python3 and throw an
            #   AttributeError on subsequent searches.
            self._do_origcurrency()

            secid = self.find('.//SECID')
            if secid is not None:
                extra_attributes = self.get('extra_attributes')
                extra_attributes['secinfo'] = secid._dereference(DBSession)
                self.set('extra_attributes', extra_attributes)

    def _postflatten(self):
        # Rename 'yield' (a reserved word in Python) to 'yld'
        attributes = self.get('attributes')
        yld = attributes.pop('yield', None)
        if yld:
            attributes['yld'] = yld
            self.set('attributes', attributes)

    def instantiate(self, DBSession, **extra_attrs):
        """
        Create an instance of a SQLAlchemy model class corresponding to
        my OFX tag, with attributes given by my contained OFX elements.

        If an instance that matches the given primary key signature has
        already been given, return that instead of creating a new one.
        """
        self.set('extra_attributes', extra_attrs)

        # SECID needs to instantiate as SECINFO
        if self.tag == 'SECID':
            SubClass = models.SECINFO
        else:
            SubClass = getattr(models, self.tag)
        self._preflatten(DBSession)
        flatattrs = self._flatten()
        self.set('attributes', flatattrs)

        self._postflatten()
        # Combine extra_attributes into attributes
        attributes = self.get('attributes')
        attributes.update(self.get('extra_attributes'))
        self.set('attributes', attributes)
        self.set('extra_attributes', {})

        try:
            fingerprint = SubClass._fingerprint(**attributes)
            instance = DBSession.query(SubClass).filter_by(**fingerprint).one()
        except NoResultFound:
            attributes = self.get('attributes')
            instance = SubClass(**attributes)
            DBSession.add(instance)

        return instance


class OFXTree(ofxtools.Parser.OFXTree):
    """ """
    element_factory = Element

    def convert(self):
        raise NotImplementedError

    def instantiate(self, DBSession):
        """ """
        if not hasattr(self, '_root'):
            raise ValueError('Must first call parse() to have data to instantiate')
        # SECLIST - list of description of securities referenced by
        # INVSTMT (investment account statement)
        seclist = self.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is not None:
            self.securities = [
                sec.instantiate(DBSession)
                for sec in seclist
            ]
            DBSession.add_all(self.securities)
        else:
            self.securities = []

        # TRNRS - transaction response, which is the main section
        # containing account statements
        #
        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        self.statements = []
        for stmtClass in (BankStatement, CreditCardStatement, InvestmentStatement):
            tagname = stmtClass._tagName
            for trnrs in self.findall('*/%sTRNRS' % tagname):
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                stmtrs = trnrs.find('%sRS' % tagname)
                if stmtrs is not None:
                    stmt = stmtClass(DBSession, stmtrs)
                    self.statements.append(stmt)


# More intuitive name for external use
OFXParser = OFXTree


### STATEMENTS
class Statement(object):
    """ Base class for Python representation of OFX *STMT aggregate """
    currency = None
    account = None

    def __init__(self, DBSession, stmtrs):
        """ Initialize with *STMTRS Element """
        self.currency = stmtrs.find('CURDEF').text
        acctfrom = stmtrs.find(self._acctTag)
        self.account = acctfrom.instantiate(DBSession)
        DBSession.add(self.account)
        self.transactions = []
        self.other_balances =[]
        self._init(DBSession, stmtrs)

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
    _tagName = 'STMT'
    _acctTag = 'BANKACCTFROM'

    def _init(self, DBSession, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            self.transactions = TransactionList(
                DBSession, self.account, tranlist,
            )
            DBSession.add_all(self.transactions)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        self.ledgerbal = ledgerbal.instantiate(DBSession, acctfrom=self.account)
        DBSession.add(self.ledgerbal)

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            self.availbal = availbal.instantiate(DBSession, acctfrom=self.account)
            DBSession.add(self.availbal)
        else:
            self.availbal = None

        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.other_balances = [bal.instantiate(DBSession) for bal in ballist]
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
    _tagName = 'INVSTMT'
    _acctTag = 'INVACCTFROM'

    def _init(self, DBSession, invstmtrs):
        dtasof = invstmtrs.find('DTASOF').text
        self.datetime = ofxtools.types.DateTime().convert(dtasof)

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            self.transactions = TransactionList(
                DBSession, self.account, tranlist
            )
            DBSession.add_all(self.transactions)

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            # FIs can list multiple INVPOS lots per security, so we
            # can't just naively instantiate what they give us or we'll
            # violate uniqueness constraints on the PKs.
            # Instead we need to manually tally up the units and instantiate
            # only a single INVPOS lot per security
            positions = {}
            for pos in poslist:
                secid = pos.find('.//SECID')
                uniqueid = secid.find('UNIQUEID')
                uniqueidtype = secid.find('UNIQUEIDTYPE')
                units = pos.find('./INVPOS/UNITS')
                seckey = (uniqueid.text, uniqueidtype.text)
                position = positions.get(seckey, None)
                if position is None:
                    positions[seckey] = (pos, Decimal(units.text))
                else:
                    positions[seckey] = (position[0],
                                         position[1] + Decimal(units.text)
                                        )
            self.positions = [pos.instantiate(
                DBSession,
                units=units, acctfrom=self.account,
                dtasof=self.datetime) \
                for pos, units in positions.values()]
            DBSession.add_all(self.positions)
        else:
            self.positions = []

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal is not None:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist is not None:
                invbal.remove(ballist)
                self.other_balances = [
                    bal.instantiate(
                        DBSession,
                        acctfrom=self.account, dtasof=self.datetime,
                    ) for bal in ballist
                ]
                DBSession.add_all(self.other_balances)
            # Now we can flatten the rest of INVBAL
            self.balances = invbal.instantiate(
                DBSession,
                acctfrom=self.account, dtasof=self.datetime,
            )
            DBSession.add(self.balances)
        else:
            self.balances = []

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
    def __init__(self, DBSession, account, tranlist):
        self.account = account
        dtstart, dtend = tranlist[0:2]
        tranlist = tranlist[2:]
        self.dtstart = ofxtools.types.DateTime().convert(dtstart.text)
        self.dtend = ofxtools.types.DateTime().convert(dtend.text)
        self.extend([self.etree_to_sql(DBSession, tran) for tran in tranlist])

    def etree_to_sql(self, DBSession, tran):
        """ Convert transaction (OFX *TRAN) """
        instance = tran.instantiate(DBSession, acctfrom=self.account)
        return instance

    def __repr__(self):
        return "<%s dtstart='%s' dtend='%s' len(self)=%d>" % \
                (self.__class__.__name__, self.dtstart, self.dtend, len(self))
