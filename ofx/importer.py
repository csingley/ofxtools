#!/usr/bin/python2.7
import sys

import elixir
import models

from utilities import _

if sys.version_info[:2] != (2, 7):
    raise RuntimeError('ofx.importer library requires Python v2.7')

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

    def processSECLIST(self):
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if not seclist:
            print "no seclist"
            return
        print "got seclst"
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

    def processSONRS(self):
        sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
        self.processSTATUS(sonrs.find('STATUS'))
        fi = sonrs.find('FI')
        if fi:
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
                self.processTRNRS(trnrs)

    def processTRNRS(self, trnrs):
        # Check the statement status
        self.processSTATUS(trnrs.find('STATUS'))
        stmtTag = trnrs.tag.replace('STMTTRNRS', 'STMTRS')
        handler = getattr(self, 'process%s' % stmtTag)
        stmt = trnrs.find(stmtTag)
        handler(stmt)

    def processSTMTRS(self, stmtrs, cc=False):
        if cc:
            acctTag = 'CCACCTFROM'
            acctClass = models.CCACCT
        else:
            acctTag = 'BANKACCTFROM'
            acctClass = models.BANKACCT
        attrs = self.flatten(stmtrs.find(acctTag))
        attrs['fi'] = self.fi
        acct = acctClass.get_or_create(**attrs)[0]

        curdef = stmtrs.find('CURDEF').text
        # STMTRS doesn't have a DTASOF element, so use LEDGERBAL.DTASOF when
        # a statement date is needed (e.g. LEDGERBAL that omits DTASOF)
        dtasof = stmtrs.find('LEDGERBAL/DTASOF').text

        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist:
            dtstart, dtend = tranlist[0:2]
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            # Silently discard DTSTART, DTEND
            for tran in tranlist:
                attrs = self.process_common(tran, acct, curdef)
                models.STMTTRN.get_or_create(**attrs)

        # LEDGERBAL - mandatory
        ledgerbal = stmtrs.find('LEDGERBAL')
        attrs = self.process_common(ledgerbal, acct, curdef)
        attrs['ledgerbal'] = attrs.pop('balamt')
        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal:
            availbal_dtasof = availbal.find('DTASOF').text
            assert availbal_dtasof.strip() == dtasof.strip()
            attrs['availbal'] = availbal.find('BALAMT').text
        models.BANKBAL.get_or_create(**attrs)

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.processBALLIST(ballist, dtasof, curdef, acct)

    def processCCSTMTRS(self, ccstmtrs):
        self.processSTMTRS(ccstmtrs, cc=True)

    def processINVSTMTRS(self, invstmtrs):
        attrs = self.flatten(invstmtrs.find('INVACCTFROM'))
        attrs['fi'] = self.fi
        acct = models.INVACCT.get_or_create(**attrs)[0]

        curdef = invstmtrs.find('CURDEF').text
        dtasof = invstmtrs.find('DTASOF').text

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist:
            dtstart, dtend = tranlist[0:2]
            # Silently discard DTSTART, DTEND
            tranlist.remove(dtstart)
            tranlist.remove(dtend)
            invbanktrans = tranlist.findall('INVBANKTRAN')
            for invbanktran in invbanktrans:
                tranlist.remove(invbanktran)
                attrs = self.process_common(invbanktran, acct, curdef)
                models.INVBANKTRAN.get_or_create(**attrs)
            for trn in tranlist:
                attrs = self.flatten(trn)
                attrs['acct'] = acct
                tranClass = getattr(models, trn.tag)
                if hasattr(tranClass, 'cursym'):
                    attrs = self.setCURSYM(attrs, curdef)
                if hasattr(tranClass, 'sec'):
                    print self.securities
                    attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'),
                                                attrs.pop('uniqueid'))]
                tranClass.get_or_create(**attrs)

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist:
            for pos in poslist:
                attrs = self.process_common(pos, acct, curdef)
                sec = attrs['sec'] = self.securities[(attrs.pop('uniqueidtype'), attrs.pop('uniqueid'))]

                # Strip out pricing data from the positions
                price_attrs = {'sec': sec}
                price_attrs.update({a: attrs.pop(a)
                    for a in ('dtpriceasof', 'unitprice', 'cursym', 'currate')})

                models.SECPRICE.get_or_create(**price_attrs)
                posClass = getattr(models, pos.tag)
                posClass.get_or_create(**attrs)

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist:
                invbal.remove(ballist)
                self.processBALLIST(ballist, dtasof, curdef, acct)
            # Now we can flatten the rest of INVBAL
            attrs = self.process_common(invbal, acct, curdef)
            attrs['dtasof'] = dtasof
            models.INVBAL.get_or_create(**attrs)

        # Unsupported subaggregates
        for tag in ('INVOOLIST', 'INV401K', 'INV401KBAL', 'MKTGINFO'):
            child = invstmtrs.find(tag)
            if child:
                invstmtrs.remove(child)

    def processBALLIST(self, ballist, dtasof, curdef, acct):
        for fibal in ballist:
            attrs = self.process_common(fibal, acct, curdef)
            attrs['dtasof'] = attrs.get('dtasof', dtasof)
            models.FIBAL.get_or_create(**attrs)

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

    ofxparser = OFXParser(verbose=args.verbose)
    ofxparser.parse(_(args.file))

    importer = OFXImporter(ofxparser.tree, verbose=args.verbose,
                            database=args.database)
    importer.process()

if __name__ == '__main__':
    main()