#!/usr/bin/env python
import sys

import elixir
import models

from utilities import _

if sys.version_info < (2, 7):
    raise RuntimeError('ofx.importer requires Python v2.7+')

class OFXResponse(object):
    """ """
    statements = []


class Statement(object):
    """ """
    account = None
    defaultCurrency = None
    dtAsOf = None
    dtStart = None
    dtEnd = None
    balance = None
    fiBalances =[]
    transactions = []

    def __init__(self, acct, curdef, dtasof):
        self.account = acct
        self.defaultCurrency = curdef
        self.dtAsOf = dtasof


class BankStatement(Statement):
    pass


class CcStatement(BankStatement):
    pass


class InvStatement(Statement):
   positions = []


class OFXImporter(object):
    """
    """
    securities = {}
    #unknown_securities = []

    def __init__(self, tree, database=None, verbose=False):
        self.tree = tree
        self.database = database
        self.verbose = verbose

        engine = elixir.sqlalchemy.create_engine(database or 'sqlite://',
                                                echo=self.verbose,
        )
        self.connection = engine.connect()
        elixir.metadata.bind = self.connection
        elixir.setup_all()
        elixir.create_all()

        self.response = OFXResponse()

    def process(self):
        try:
            self.processSECLIST()
            self.processSONRS()
            self.processStatements()
        except:
            elixir.session.rollback()
            raise
        else:
            elixir.session.commit()

    def processSECLIST(self):
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is None:
            return
        for sec in seclist:
            # Strip MFASSETCLASS/FIMFASSETCLASS - lists that will blow up flatten()
            mfassetclass = sec.find('MFASSETCLASS')
            if mfassetclass:
                sec.remove(mfassetclass)
            fimfassetclass = sec.find('FIMFASSETCLASS')
            if fimfassetclass:
                sec.remove(fimfassetclass)
            secClass = getattr(models, sec.tag)
            attrs = self.flatten(sec)
            instance = secClass.match(**attrs)
            if instance:
                # Create Securities instances, and store in a map of
                #  (uniqueidtype, uniqueid) -> Security for quick lookup
                #
                # The logic in models.SECINFO.match() doesn't require that the
                # securities instance matched from the DB has the same key
                # (uniqueidtype, uniqueid) as the attributes incoming from the
                # OFX file currently being processed.  So make sure to key the
                # dict according to the current attributes, not the DB's.
                self.securities[(attrs['uniqueidtype'], attrs['uniqueid'])] = instance
            else:
                # FIXME - shouldn't just blindly create unknown securities
                instance = secClass(**attrs)
                if mfassetclass:
                    for portion in mfassetclass:
                        attrs = self.flatten(portion)
                        attrs['mf'] = instance
                        models.MFASSETCLASS.get_or_create(**attrs)
                if fimfassetclass:
                    for portion in fimfassetclass:
                        attrs = self.flatten(portion)
                        attrs['mf'] = instance
                        models.FIMFASSETCLASS.get_or_create(**attrs)
                # Create Securities instances, and store in a map of
                #  (uniqueidtype, uniqueid) -> Security for quick lookup
                self.securities[(instance.uniqueidtype, instance.uniqueid)] = instance

    def processSONRS(self):
        sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
        self.processSTATUS(sonrs.find('STATUS'))
        fi = sonrs.find('FI')
        if fi is not None:
            attrs = self.flatten(fi)
            fi = models.FI.get_or_create(**attrs)[0]
        self.fi = fi

    def processSTATUS(self, status):
        attrs = self.flatten(status)
        severity = attrs['severity']
        assert severity in ('INFO', 'WARN', 'ERROR')
        if severity == 'ERROR':
            # FIXME - handle errors
            raise ValueError
        elif severity == 'WARN':
            # FIXME - handle errors
            raise ValueError

    def processStatements(self):
        for tag in ('STMTTRNRS', 'CCSTMTTRNRS', 'INVSTMTTRNRS'):
            for trnrs in self.tree.findall('*/%s' % tag):
                self.response.statements.append(self.processTRNRS(trnrs))

    def processTRNRS(self, trnrs):
        # Check the statement status
        self.processSTATUS(trnrs.find('STATUS'))
        stmtTag = trnrs.tag.replace('STMTTRNRS', 'STMTRS')
        handler = getattr(self, 'process%s' % stmtTag)
        stmt = trnrs.find(stmtTag)
        return handler(stmt)

    def processSTMTRS(self, stmtrs, cc=False):
        if cc:
            acctTag = 'CCACCTFROM'
            acctClass = models.CCACCT
            statementClass = CcStatement
        else:
            acctTag = 'BANKACCTFROM'
            acctClass = models.BANKACCT
            statementClass = BankStatement
        attrs = self.flatten(stmtrs.find(acctTag))
        attrs['fi'] = self.fi
        acct = acctClass.get_or_create(**attrs)[0]

        curdef = stmtrs.find('CURDEF').text

        # STMTRS doesn't have a DTASOF element, so use LEDGERBAL.DTASOF when
        # a statement date is needed (e.g. BALLIST.BAL that omits DTASOF)
        dtasof = stmtrs.find('LEDGERBAL/DTASOF').text

        statement = statementClass(acct, curdef, models.OFXDtConverter.to_python(dtasof))

        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            statement.dtstart = models.OFXDtConverter.to_python(dtstart.text)
            statement.dtend = models.OFXDtConverter.to_python(dtend.text)
            for tran in tranlist:
                attrs = self.process_common(tran, acct, curdef)
                statement.transactions.append(models.STMTTRN.get_or_create(**attrs)[0])

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        attrs = self.process_common(ledgerbal, acct, curdef)
        attrs['ledgerbal'] = attrs.pop('balamt')
        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            availbal_dtasof = availbal.find('DTASOF').text
            assert availbal_dtasof.strip() == dtasof.strip()
            attrs['availbal'] = availbal.find('BALAMT').text
        statement.balance = models.BANKBAL.get_or_create(**attrs)[0]

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            statement.fibals = self.processBALLIST(ballist, dtasof, curdef, acct)

        return statement

    def processCCSTMTRS(self, ccstmtrs):
        self.processSTMTRS(ccstmtrs, cc=True)

    def processINVSTMTRS(self, invstmtrs):
        attrs = self.flatten(invstmtrs.find('INVACCTFROM'))
        attrs['fi'] = self.fi
        acct = models.INVACCT.get_or_create(**attrs)[0]

        curdef = invstmtrs.find('CURDEF').text
        dtasof = invstmtrs.find('DTASOF').text

        statement = InvStatement(acct, curdef, models.OFXDtConverter.to_python(dtasof))

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            dtstart, dtend = tranlist[0:2]
            # Silently discard DTSTART, DTEND
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            statement.dtstart = models.OFXDtConverter.to_python(dtstart.text)
            statement.dtend = models.OFXDtConverter.to_python(dtend.text)
            invbanktrans = tranlist.findall('INVBANKTRAN')
            for invbanktran in invbanktrans:
                tranlist.remove(invbanktran)
                attrs = self.process_common(invbanktran, acct, curdef)
                statement.transactions.append(models.INVBANKTRAN.get_or_create(**attrs)[0])
            for trn in tranlist:
                attrs = self.flatten(trn)
                attrs['acct'] = acct
                tranClass = getattr(models, trn.tag)
                if hasattr(tranClass, 'cursym'):
                    attrs = self.setCURSYM(attrs, curdef)
                if hasattr(tranClass, 'sec'):
                    attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'),
                                                attrs.pop('uniqueid'))]
                statement.transactions.append(tranClass.get_or_create(**attrs)[0])

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            for pos in poslist:
                attrs = self.process_common(pos, acct, curdef)
                sec = attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'), attrs.pop('uniqueid'))]

                # Strip out pricing data from the positions
                price_attrs = {'sec': sec}
                price_attrs.update({a: attrs.pop(a)
                    for a in ('dtpriceasof', 'unitprice', 'cursym', 'currate')})

                # FIXME - pricing data not yet captured in OFXResponse.statements
                models.SECPRICE.get_or_create(**price_attrs)

                posClass = getattr(models, pos.tag)
                statement.positions.append(posClass.get_or_create(**attrs)[0])

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal is not None:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist is not None:
                invbal.remove(ballist)
                self.processBALLIST(ballist, dtasof, curdef, acct)
            # Now we can flatten the rest of INVBAL
            attrs = self.process_common(invbal, acct, curdef)
            attrs['dtasof'] = dtasof
            statement.balances = models.INVBAL.get_or_create(**attrs)[0]

        # Unsupported subaggregates
        for tag in ('INVOOLIST', 'INV401K', 'INV401KBAL', 'MKTGINFO'):
            child = invstmtrs.find(tag)
            if child:
                invstmtrs.remove

        return statement

    def processBALLIST(self, ballist, dtasof, curdef, acct):
        def processBAL(fibal):
            attrs = self.process_common(fibal, acct, curdef)
            attrs['dtasof'] = attrs.get('dtasof', dtasof)
            return models.FIBAL.get_or_create(**attrs)[0]
        return [processBAL(fibal) for fibal in ballist]
        #for fibal in ballist:
            #attrs = self.process_common(fibal, acct, curdef)
            #attrs['dtasof'] = attrs.get('dtasof', dtasof)
            #models.FIBAL.get_or_create(**attrs)

    def flatten(self, element):
        """
        Recurse through aggregate and flatten; return an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
        """
        aggregates = {}
        leaves = {}
        for child in element:
            tag = child.tag
            data = child.text
            if data is not None:
                data = data.strip()
            if data:
                # element is a leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # element is an aggregate.
                assert tag not in aggregates
                aggregates.update(self.flatten(child))
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggregates.keys():
            assert key not in leaves
        leaves.update(aggregates)
        return leaves

    def setCURSYM(self, attrs, curdef):
        """
        Set CURSYM (currency) to CURDEF (default currency) if necessary.
        Takes a dict as input; returns a dict.
        """
        has_cursym = 'cursym' in attrs
        has_origcursym = 'origcursym' in attrs
        # OFX spec insists CURSYM and ORIGCURSYM be mutually exclusive
        assert not (has_cursym and has_origcursym)
        if not (has_cursym or has_origcursym):
            attrs['cursym'] = curdef
            attrs['currate'] = 1
        return attrs

    def process_common(self, element, acct, curdef):
        attrs = self.flatten(element)
        attrs = self.setCURSYM(attrs, curdef)
        attrs['acct'] = acct
        return attrs


def main():
    from argparse import ArgumentParser
    from parser import OFXParser

    argparser = ArgumentParser()
    argparser.add_argument('file')
    argparser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Turn on debug output')
    argparser.add_argument('-d', '--database',
                        help='URL of persistent database')
    args = argparser.parse_args()

    tree = OFXParser()
    tree.parse(_(args.file))

    importer = OFXImporter(tree.getroot(), verbose=args.verbose,
                            database=args.database)
    importer.process()
    print importer.response.statements

if __name__ == '__main__':
    main()