#!/usr/bin/env python
import elixir
import models

class OFXImporter(object):
    """
    """
    securities = {}
    unknown_securities = []

    def __init__(self, tree, database=None, verbose=False):
        self.tree = tree
        self.database = database
        self.verbose = verbose

        engine = elixir.sqlalchemy.create_engine(database or 'sqlite://',
                                                echo=self.verbose)
        self.connection = engine.connect()
        elixir.metadata.bind = self.connection
        elixir.setup_all()
        elixir.create_all()

    def process(self):
        try:
            self.processSECLIST()
            # FIXME - shouldn't just blindly create unknown_securities
            for secClass, attrs, mfassetclass, fimfassetclass in self.unknown_securities:
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
            self.processSONRS()
            self.processStatements()
        except:
            elixir.session.rollback()
            raise
        else:
            elixir.session.commit()

    def processSONRS(self):
        sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
        self.processSTATUS(sonrs.find('STATUS'))
        fi = sonrs.find('FI')
        if fi:
            attrs = self.flatten(fi)
            fi = models.FI.get_or_create(**attrs)[0]
        self.fi = fi

    def processSECLIST(self):
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if not seclist:
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
                self.securities[(instance.uniqueidtype, instance.uniqueid)] = instance
            else:
                self.unknown_securities.append((secClass, attrs, mfassetclass, fimfassetclass))

    def processStatements(self):
        for tag in ('STMTTRNRS', 'CCSTMTTRNRS', 'INVSTMTTRNRS'):
            for trnrs in self.tree.findall('*/%s' % tag):
                self.processTRNRS(trnrs)

    def processTRNRS(self, trnrs):
        # Check the statement status
        self.processSTATUS(trnrs.find('STATUS'))
        stmtTag = trnrs.tag.replace('STMTTRNRS', 'STMTRS')
        handler = getattr(self, 'process%s' % stmtTag)
        stmt = trnrs.find(stmtTag)
        handler(stmt)

    def flatten(self, element):
        """
        Recurse through aggregate and flatten into an un-nested dict.

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

    def processSTMTRS(self, element, cc=False):
        if cc:
            acctTag = 'CCACCTFROM'
            acctClass = models.CCACCT
        else:
            acctTag = 'BANKACCTFROM'
            acctClass = models.BANKACCT
        acct_attrs = self.flatten(element.find(acctTag))
        acct_attrs['fi'] = self.fi
        acct = acctClass.get_or_create(**acct_attrs)[0]

        curdef = element.find('CURDEF').text

        # BANKTRANLIST
        tranlist = element.find('BANKTRANLIST')
        if tranlist:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            for tran in tranlist:
                attrs = self.flatten(tran)
                attrs = self.setCURSYM(attrs, curdef)
                attrs['acct'] = acct
                models.STMTTRN.get_or_create(**attrs)

        # LEDGERBAL - mandatory
        ledgerbal = element.find('LEDGERBAL')
        attrs = self.flatten(ledgerbal)
        attrs['ledgerbal'] = attrs.pop('balamt')
        self.setCURSYM(attrs, curdef)
        availbal = element.find('AVAILBAL')
        if availbal:
            # FIXME - check that AVAILBAL.DTASOF matches LEDGERBAL.DTASOF
            attrs['availbal'] = availbal.find('BALAMT').text
        attrs['acct'] = acct
        models.BANKBAL.get_or_create(**attrs)

        # BALLIST
        ballist = element.find('BALLIST')
        if ballist:
            for fibal in ballist:
                attrs = self.flatten(fibal)
                self.setCURSYM(attrs, curdef)
                attrs['acct'] = acct
                models.FIBAL.get_or_create(**attrs)

    def processCCSTMTRS(self, element):
        self.processSTMTRS(element, cc=True)

    def setCURSYM(self, attrs, curdef):
        has_cursym = 'cursym' in attrs
        has_origcursym = 'origcursym' in attrs
        # OFX spec insists CURSYM and ORIGCURSYM be mutually exclusive
        assert not (has_cursym and has_origcursym)
        if not (has_cursym or has_origcursym):
            attrs['cursym'] = curdef
            attrs['currate'] = 1
        return attrs

    def processINVSTMTRS(self, element):
        attrs = self.flatten(element.find('INVACCTFROM'))
        attrs['fi'] = self.fi
        acct = models.INVACCT.get_or_create(**attrs)[0]

        curdef = element.find('CURDEF').text
        dtasof = element.find('DTASOF').text

        # INVTRANLIST
        tranlist = element.find('INVTRANLIST')
        if tranlist:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)

            invbanktrans = tranlist.findall('INVBANKTRAN')
            for invbanktran in invbanktrans:
                tranlist.remove(invbanktran)
                attrs = self.flatten(invbanktran)
                attrs = self.setCURSYM(attrs, curdef)
                attrs['acct'] = acct
                models.INVBANKTRAN.get_or_create(**attrs)
            for trn in tranlist:
                tranClass = getattr(models, trn.tag)
                attrs = self.flatten(trn)
                # Securities-related transactions
                if issubclass(tranClass, (models.INVBUY, models.INVSELL, models.CLOSUREOPT,
                                        models.INCOME, models.INVEXPENSE, models.JRNLSEC,
                                        models.REINVEST, models.RETOFCAP, models.SPLIT,
                                        models.TRANSFER)):
                    attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'),
                                                attrs.pop('uniqueid'))]
                # Transactions with currency
                if issubclass(tranClass, (models.INVBUY, models.INVSELL, models.INCOME,
                                        models.INVEXPENSE, models.MARGININTEREST,
                                        models.REINVEST, models.RETOFCAP)):
                    attrs = self.setCURSYM(attrs, curdef)
                attrs['acct'] = acct
                #attrs['stmtrs'] = stmtrs
                tranClass.get_or_create(**attrs)

        # INVPOSLIST
        poslist = element.find('INVPOSLIST')
        if poslist:
            for pos in poslist:
                posClass = getattr(models, pos.tag)
                attrs = self.flatten(pos)
                attrs['acct'] = acct
                sec = attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'), attrs.pop('uniqueid'))]

                # Strip out pricing data from the positions
                price_attrs = {'sec': sec}
                price_attrs.update(dict([(a, attrs.pop(a, None))
                    for a in ('dtpriceasof', 'unitprice', 'cursym', 'currate')]))
                price_attrs['cursym'] = price_attrs['cursym'] or curdef

                models.SECPRICE.get_or_create(**price_attrs)
                posClass.get_or_create(**attrs)

        # INVBAL
        invbal = element.find('INVBAL')
        if invbal:
            # Strip off BALLIST
            ballist = invbal.find('BALLIST')
            if ballist:
                invbal.remove(ballist)
                for fibal in ballist:
                    attrs = self.flatten(fibal)
                    attrs['acct'] = acct
                    # FIXME - check that BAL.DTASOF (if present) matches INVSTMTRS.DTASOF
                    attrs['dtasof'] = dtasof
                    self.setCURSYM(attrs, curdef)
                    models.FIBAL.get_or_create(**attrs)
            attrs = self.flatten(invbal)
            attrs['acct'] = acct
            attrs['dtasof'] = dtasof
            attrs['cursym'] = curdef
            attrs['currate'] = 1
            models.INVBAL.get_or_create(**attrs)

        # INVOOLIST - not supported
        invoolist = element.find('INVOOLIST')
        if invoolist:
            element.remove(invoolist)

        # INV401K - not supported
        inv401k = element.find('INV401K')
        if inv401k:
            element.remove(inv401k)

        # INV401KBAL - not supported
        inv401kbal = element.find('INV401KBAL')
        if inv401kbal:
            element.remove(inv401kbal)

        # MKTGINFO - not supported
        mktginfo = element.find('MKTGINFO')
        if mktginfo:
            element.remove(mktginfo)

def main():
    import sys
    from optparse import OptionParser
    from parser import OFXParser
    optparser = OptionParser(usage='usage: %prog FILE')
    optparser.set_defaults(verbose=False, database=None)
    optparser.add_option('-v', '--verbose', action='store_true',
                        help='Turn on debug output')
    optparser.add_option('-d', '--database',
                        help='URL of persistent database')
    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.print_usage()
        sys.exit(-1)
    FILE = args[0]

    ofxparser = OFXParser(verbose=options.verbose)
    ofxparser.parse(FILE)
    importer = OFXImporter(ofxparser.tree, verbose=options.verbose,
                            database=options.database)
    importer.process()

if __name__ == '__main__':
    main()