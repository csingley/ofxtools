#!/usr/bin/env python
import sys

import converters

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

    def __init__(self, tree):
        self.tree = tree
        self.response = OFXResponse()

    def process(self):
        #self.processSECLIST()
        self.processSONRS()
        self.processStatements()

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
            secClass = getattr(converters, sec.tag)
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
            fi = converters.FI(**attrs)
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
            acctClass = converters.CCACCT
            statementClass = CcStatement
        else:
            acctTag = 'BANKACCTFROM'
            acctClass = converters.BANKACCT
            statementClass = BankStatement
        attrs = self.flatten(stmtrs.find(acctTag))
        acct = acctClass(**attrs)

        curdef = stmtrs.find('CURDEF').text

        # STMTRS doesn't have a DTASOF element, so use LEDGERBAL.DTASOF when
        # a statement date is needed (e.g. BALLIST.BAL that omits DTASOF)
        dtasof = stmtrs.find('LEDGERBAL/DTASOF').text

        statement = statementClass(acct, curdef, converters.DateTime.convert(dtasof))

        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)

            statement.dtStart = converters.DateTime.convert(dtstart.text)
            statement.dtEnd = converters.DateTime.convert(dtend.text)
            for tran in tranlist:
                attrs = self.process_common(tran, acct, curdef)
                statement.transactions.append(converters.STMTTRN(**attrs))

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
        statement.balance = converters.BANKBAL(**attrs)

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            statement.fibals = self.processBALLIST(ballist, dtasof, curdef, acct)

        return statement

    def processCCSTMTRS(self, ccstmtrs):
        self.processSTMTRS(ccstmtrs, cc=True)

    def processINVSTMTRS(self, invstmtrs):
        attrs = self.flatten(invstmtrs.find('INVACCTFROM'))
        acct = converters.INVACCT(**attrs)

        curdef = invstmtrs.find('CURDEF').text
        dtasof = invstmtrs.find('DTASOF').text

        statement = InvStatement(acct, curdef, converters.DateTime.convert(dtasof))

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            dtstart, dtend = tranlist[0:2]
            # Silently discard DTSTART, DTEND
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            statement.dtStart = converters.DateTime.convert(dtstart.text)
            statement.dtEnd = converters.DateTime.convert(dtend.text)
            invbanktrans = tranlist.findall('INVBANKTRAN')
            for invbanktran in invbanktrans:
                tranlist.remove(invbanktran)
                attrs = self.process_common(invbanktran, acct, curdef)
                statement.transactions.append(converters.INVBANKTRAN(**attrs))
            for trn in tranlist:
                attrs = self.flatten(trn)
                tranClass = getattr(converters, trn.tag)
                if hasattr(tranClass, 'cursym'):
                    attrs = self.setCURSYM(attrs, curdef)
                if hasattr(tranClass, 'sec'):
                    attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'),
                                                attrs.pop('uniqueid'))]
                statement.transactions.append(tranClass(**attrs))

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            for pos in poslist:
                attrs = self.process_common(pos, acct, curdef)

                ## Strip out pricing data from the positions
                #price_attrs = {'sec': sec}
                #price_attrs.update({a: attrs.pop(a)
                    #for a in ('dtpriceasof', 'unitprice', 'cursym', 'currate')})

                ## FIXME - pricing data not yet captured in OFXResponse.statements
                #models.SECPRICE.get_or_create(**price_attrs)

                posClass = getattr(converters, pos.tag)
                statement.positions.append(posClass(**attrs))

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
            statement.balances = converters.INVBAL(**attrs)

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
            return converters.FIBAL(**attrs)
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
        return attrs


def main():
    from argparse import ArgumentParser
    from parser import OFXParser

    argparser = ArgumentParser()
    argparser.add_argument('file')
    args = argparser.parse_args()

    tree = OFXParser()
    tree.parse(_(args.file))

    importer = OFXImporter(tree.getroot())
    importer.process()


if __name__ == '__main__':
    main()