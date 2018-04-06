# coding: utf-8
"""
Version of ofxtools.Parser that uses SQLAlchemy for conversion
"""
# stdlib imports
from decimal import Decimal

# 3rd party imports
from sqlalchemy.orm.exc import NoResultFound


# local imports
import ofxtools
from ofxtools.ofxalchemy.database import Session
from ofxtools.ofxalchemy import models


class OFXTree(ofxtools.Parser.OFXTree):
    """ """
    def convert(self):
        raise NotImplementedError

    def instantiate(self):
        """ """
        if not hasattr(self, '_root'):
            raise ValueError(
                'Must first call parse() to have data to instantiate'
            )

        # SECLIST - list of description of securities referenced by
        # INVSTMT (investment account statement)
        seclist = self.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is not None:
            self.securities = [
                self._instantiate(sec)
                for sec in seclist
            ]
        else:
            self.securities = []

        # TRNRS - transaction response, which is the main section
        # containing account statements
        #
        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        self.statements = []
        for stmtClass in (
            BankStatement, CreditCardStatement, InvestmentStatement
        ):
            tagname = stmtClass._tagName
            for trnrs in self.findall('*/%sTRNRS' % tagname):
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                stmtrs = trnrs.find('%sRS' % tagname)
                if stmtrs is not None:
                    stmt = stmtClass(stmtrs)
                    self.statements.append(stmt)

    @classmethod
    def _flatten(cls, elem):
        """
        Recurse through aggregate and flatten; return an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
        """
        aggs = {}
        leaves = {}
        for child in elem:
            tag = child.tag
            data = child.text or ''
            data = data.strip()
            if data:
                # it's a data-bearing leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # it's an aggregate.
                assert tag not in aggs
                aggs.update(cls._flatten(child))
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggs.keys():
            assert key not in leaves
        leaves.update(aggs)

        return leaves

    @classmethod
    def _dereference(cls, elem):
        """ """
        reference = cls._instantiate(elem)
        elem.clear()
        return reference

    @classmethod
    def _do_origcurrency(cls, elem):
        """
        See OFX spec section 5.2 for currency handling conventions.
        Flattening the currency definition leaves only the CURRATE/CURSYM
        elements, leaving no indication of whether these were sourced from
        a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        important to interpreting transactions in foreign correncies, we
        preserve this information by adding a nonstandard curtype element.
        """
        currency = elem.find('*/CURRENCY')
        origcurrency = elem.find('*/ORIGCURRENCY')
        if (currency is not None) or (origcurrency is not None):
            if (currency is not None) and (origcurrency is not None):
                msg = '<%s> may not contain both <CURRENCY> and <ORIGCURRENCY>' % elem.tag
                raise ofxtools.Parser.ParseError(msg)
            curtype = currency
            if curtype is None:
                curtype = origcurrency
            if (curtype is not None):
                extra_attributes = elem.get('extra_attributes')
                extra_attributes['curtype'] = curtype.tag
                elem.set('extra_attributes', extra_attributes)

    @classmethod
    def _preflatten(cls, elem):
        """ """
        if elem.tag == 'OPTINFO':
            # A <SECID> aggregate referring to the security underlying the
            # option is, in general, *not* going to be contained in <SECLIST>
            # (because you don't necessarily have a position in the underlying).
            # Since the <SECID> for the underlying only gives us fields for
            # (uniqueidtype, uniqueid) we can't really go ahead and use this
            # information to create a corresponding SECINFO instance (since we
            # lack information about the security subclass).  It's unclear that
            # the SECID of the underlying is really needed for anything, so we
            # disregard it.
            secid = elem.find('./SECID')
            if secid is not None:
                elem.remove(secid)

        elif elem.tag == 'MFINFO':
            # Strip {MF, FIMF}ASSETCLASS - lists that will blow up _flatten()
            # These are nearly useless for asset allocation since they're
            # so unreliable.  Since they're also a lot of trouble to process,
            # we're just going to delete them.
            #
            # Do all XPath searches before removing nodes from the tree
            #   which seems to mess up the DOM in Python3 and throw an
            #   AttributeError on subsequent searches.
            mfassetclass = elem.find('./MFASSETCLASS')
            fimfassetclass = elem.find('./FIMFASSETCLASS')

            if mfassetclass is not None:
                elem.remove(mfassetclass)
            if fimfassetclass is not None:
                elem.remove(fimfassetclass)

        elif elem.tag.startswith('POS'):
            secid = elem.find('.//SECID')
            if secid is None:
                msg = '<%s> does not contain <SECID>'
                raise ofxtools.Parser.ParseError(msg)
            extra_attributes = elem.get('extra_attributes')
            extra_attributes['secinfo'] = cls._dereference(secid)
            elem.set('extra_attributes', extra_attributes)

        elif elem.tag in ('STMTTRN', 'INVBANKTRAN'):
            # Replace BANKACCTTO/CCACCTTO/PAYEE with FK references.  This is
            # needed for {BANK,CC}ACCTTO because account type information is
            # contained in the aggregate container, which will be lost by
            # _flatten().  PAYEE will not lose information when _flatten()ed,
            # but it really needs its own object class to be useful.
            #
            # Do all XPath searches before removing nodes from the tree
            #   which seems to mess up the DOM in Python3 and throw an
            #   AttributeError on subsequent searches.
            bankacctto = elem.find('BANKACCTTO')
            ccacctto = elem.find('CCACCTTO')
            payee = elem.find('PAYEE')

            cls._do_origcurrency(elem)

            if bankacctto is not None:
                extra_attributes = elem.get('extra_attributes')
                extra_attributes['acctto'] = cls._dereference(bankacctto)
                elem.set('extra_attributes', extra_attributes)
            if ccacctto is not None:
                extra_attributes = elem.get('extra_attributes')
                extra_attributes['acctto'] = cls._dereference(ccacctto)
                elem.set('extra_attributes', extra_attributes)
            if (bankacctto is not None) and (ccacctto is not None):
                msg = '<%s> may not contain both <BANKACCTTO> and <CCACCTTO>' % elem.tag
                raise ofxtools.Parser.ParseError(msg)
            if payee is not None:
                extra_attributes = elem.get('extra_attributes')
                extra_attributes['payee'] = cls._dereference(payee)
                elem.set('extra_attributes', extra_attributes)

        elif elem.find('.//INVTRAN') is not None:
            # Do all XPath searches before removing nodes from the tree
            #   which seems to mess up the DOM in Python3 and throw an
            #   AttributeError on subsequent searches.
            cls._do_origcurrency(elem)

            secid = elem.find('.//SECID')
            if secid is not None:
                extra_attributes = elem.get('extra_attributes')
                extra_attributes['secinfo'] = cls._dereference(secid)
                elem.set('extra_attributes', extra_attributes)

    @classmethod
    def _postflatten(cls, elem):
        # Rename 'yield' (a reserved word in Python) to 'yld'
        attributes = elem.get('attributes')
        yld = attributes.pop('yield', None)
        if yld:
            attributes['yld'] = yld
            elem.set('attributes', attributes)

    @classmethod
    def _instantiate(cls, elem, **extra_attrs):
        """
        Create an instance of a SQLAlchemy model class corresponding to
        my OFX tag, with attributes given by my contained OFX elements.

        If an instance that matches the given primary key signature has
        already been given, return that instead of creating a new one.
        """
        elem.set('extra_attributes', extra_attrs)

        cls._preflatten(elem)
        flatattrs = cls._flatten(elem)
        elem.set('attributes', flatattrs)

        cls._postflatten(elem)
        # Combine extra_attributes into attributes
        attributes = elem.get('attributes')
        attributes.update(elem.get('extra_attributes'))
        elem.set('attributes', attributes)
        elem.set('extra_attributes', {})

        # SECID needs to instantiate as SECINFO
        if elem.tag == 'SECID':
            LookupSubclass = models.SECINFO
            # A SECID aggregate refers to a SECINFO that should be known from
            # SECLIST.  We really don't want to be seeing a CUSIP for the
            # first time here and then persisting it as the SECINFO
            # superclass (which doesn't exist in the OFX spec) rather than
            # a DEBTINFO, STOCKINFO, or other subclass.
            Subclass = None
        else:
            Subclass = getattr(models, elem.tag)

            # Some brokers (*cough* *cough* IBKR *cough* *cough*) are in the
            # habit of arbitrarily changing the SECINFO subclass of a security
            # (e.g. for reorgs where they don't know what the hell they've
            # received, the same CUSIP will be given as an OTHERINFO in one
            # response, and a DEBTINFO in another response).  This breaks our
            # inheritance model, which defines a
            # UniqueConstraint(uniqueid, uniqueidtype) on the SECINFO
            # superclass, and therefore throws a violation error when  we try
            # to persist a DEBTINFO with the same fingerprint as an existing
            # OTHERINFO.
            #
            # To deal with this, we have all SECINFO subclasses look up their
            # surrogate primary key on the superclass itself rather than the
            # subclass.  Upon instantiation all subsequent OFX aggregates
            # will have their data changed to refer to the first imported
            # SECINFO subclass with a given CUSIP.  We lose information this
            # way, but the information isn't terribly significant (as evidenced
            # by FIs constantly screwing this up without Quicken users throwing
            # a fit about it) and certainly far less important than maintaining
            # database consistency.
            if issubclass(Subclass, models.SECINFO):
                LookupSubclass = models.SECINFO
            else:
                LookupSubclass = Subclass

        try:
            fingerprint = LookupSubclass._fingerprint(**attributes)
            instance = LookupSubclass.query.filter_by(**fingerprint).one()
        except NoResultFound:
            if not Subclass:
                msg = '%s finds no corresponding %s instance with %s' % (
                    elem.tag, LookupSubclass.__name__, fingerprint
                )
                raise ofxtools.Parser.ParseError(msg)
            attributes = elem.get('attributes')
            instance = Subclass(**attributes)
            Session.add(instance)

        return instance


# More intuitive name for external use
OFXParser = OFXTree


### STATEMENTS
class Statement(object):
    """ Base class for Python representation of OFX *STMT aggregate """
    currency = None
    account = None

    def __init__(self, stmtrs):
        """ Initialize with *STMTRS Element """
        self.currency = stmtrs.find('CURDEF').text
        acctfrom = stmtrs.find(self._acctTag)
        self.account = OFXTree._instantiate(acctfrom)
        self.transactions = []
        self.other_balances = []
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
    _tagName = 'STMT'
    _acctTag = 'BANKACCTFROM'

    def _init(self, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            self.transactions = TransactionList(self.account, tranlist,)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        self.ledgerbal = OFXTree._instantiate(ledgerbal, acctfrom=self.account)

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            self.availbal = OFXTree._instantiate(availbal,acctfrom=self.account)
        else:
            self.availbal = None

        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.other_balances = [OFXTree._instantiate(bal) for bal in ballist]

        # Unsupported subaggregates
        for tag in ('MKTGINFO', ):
            child = stmtrs.find(tag)
            if child:
                stmtrs.remove(child)

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

    def _init(self, invstmtrs):
        dtasof = invstmtrs.find('DTASOF').text
        self.datetime = ofxtools.Types.DateTime().convert(dtasof)

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            self.transactions = TransactionList(
                self.account, tranlist
            )

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
            self.positions = [OFXTree._instantiate(
                pos, units=units, acctfrom=self.account,
                dtasof=self.datetime)
                for pos, units in positions.values()]
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
                    OFXTree._instantiate(
                        bal, acctfrom=self.account, dtasof=self.datetime,
                    ) for bal in ballist
                ]
            # Now we can flatten the rest of INVBAL
            self.balances = OFXTree._instantiate(
                invbal, acctfrom=self.account, dtasof=self.datetime,
            )
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
    def __init__(self, account, tranlist):
        self.account = account
        dtstart, dtend = tranlist[0:2]
        tranlist = tranlist[2:]
        self.dtstart = ofxtools.Types.DateTime().convert(dtstart.text)
        self.dtend = ofxtools.Types.DateTime().convert(dtend.text)
        self.extend([self.etree_to_sql(tran) for tran in tranlist])

    def etree_to_sql(self, tran):
        """ Convert transaction (OFX *TRAN) """
        instance = OFXTree._instantiate(tran, acctfrom=self.account)
        return instance

    def __repr__(self):
        return "<%s dtstart='%s' dtend='%s' len(self)=%d>" % \
                (self.__class__.__name__, self.dtstart, self.dtend, len(self))


def main():
    from argparse import ArgumentParser
    from ofxtools.ofxalchemy.database import init_db, sessionmanager

    argparser = ArgumentParser(description='Import OFX data')
    argparser.add_argument('-d', '--database', default='sqlite://',
                           help='Database connection')
    argparser.add_argument('file', nargs='+', help='OFX file(s)')
    args = argparser.parse_args()

    init_db(args.database)

    for file in args.file:
        ofxparser = OFXTree()
        with sessionmanager() as session:
            ofxparser.parse(file)
            ofxparser.instantiate()


if __name__ == '__main__':
    main()
