# coding: utf-8

# stdlib imports
import unittest


# local imports
# import ofxtools
# from ofxtools.models.base import Aggregate


# def ofx_parse(filename):
    # tree = ofxtools.Parser.OFXTree()
    # tree.parse(filename)
    # return tree.convert()


# class ParserTestCase(unittest.TestCase):
    # def assert_result(self, result):
        # expected_attributes = ['securities', 'sonrs', 'statements', 'tree']
        # result_attributes = dir(result)
        # for attribute in expected_attributes:
            # self.assertIn(attribute, result_attributes)

    # def test_account_type_checking(self):
        # filename = 'tests/data/stmtrs.ofx'
        # result = ofx_parse(filename)
        # self.assert_result(result)
        # # TODO: do something with 'result'

    # def test_euro_decimal_separator(self):
        # filename = 'tests/data/stmtrs_euro.ofx'
        # result = ofx_parse(filename)
        # self.assert_result(result)
        # # TODO: do something with 'result'

    # def test_account_type_investment(self):
        # filename = 'tests/data/invstmtrs.ofx'
        # result = ofx_parse(filename)
        # self.assert_result(result)


# with open('tests/data/stmtrs.ofx') as f:
    # # Strip the OFX header
    # sgml = ''.join(f.readlines()[3:])
    # parser = ofxtools.Parser.TreeBuilder()
    # parser.feed(sgml)
    # ofx = parser.close()


# class TreeBuilderTestCase(unittest.TestCase):
    # def aggregate(self, node, tag, num_children):
        # """ Test OFX 'aggregate', i.e. non-data-bearing branch node """
        # self.assertEqual(node.tag, tag)
        # self.assertEqual(len(node), num_children)
        # self.assertIsNone(node.text)
        # self.assertEqual(node.attrib, {})

    # def element(self, node, tag, data):
        # """ Test OFX 'element', i.e. data-bearing leaf node """
        # self.assertEqual(node.tag, tag)
        # self.assertEqual(len(node), 0)
        # self.assertEqual(node.text, data)
        # self.assertEqual(node.attrib, {})

    # def test_parse(self):
        # self.assertEqual(ofx.tag, 'OFX')
        # self.aggregate(ofx, tag='OFX', num_children=2)

        # # <SIGNONMSGSRSV1>
        # signon = ofx[0]
        # self.aggregate(signon, tag='SIGNONMSGSRSV1', num_children=1)

        # # <SIGNONMSGSRSV1> - <SONRS>
        # sonrs = signon[0]
        # self.aggregate(sonrs, tag='SONRS', num_children=6)

        # # <SIGNONMSGSRSV1> - <SONRS> - <STATUS>
        # status = sonrs[0]
        # self.aggregate(status, tag='STATUS', num_children=2)

        # # <SIGNONMSGSRSV1> - <SONRS> - <STATUS> - <CODE>
        # code = status[0]
        # self.element(code, tag='CODE', data='0')

        # # <SIGNONMSGSRSV1> - <SONRS> - <STATUS> - <SEVERITY>
        # severity = status[1]
        # self.element(severity, tag='SEVERITY', data='INFO')

        # # <SIGNONMSGSRSV1> - <SONRS> - <DTSERVER>
        # dtserver = sonrs[1]
        # self.element(dtserver, tag='DTSERVER', data='20051029101003')

        # # <SIGNONMSGSRSV1> - <SONRS> - <LANGUAGE>
        # language = sonrs[2]
        # self.element(language, tag='LANGUAGE', data='ENG')

        # # <SIGNONMSGSRSV1> - <SONRS> - <DTPROFUP>
        # dtprofup = sonrs[3]
        # self.element(dtprofup, tag='DTPROFUP', data='19991029101003')

        # # <SIGNONMSGSRSV1> - <SONRS> - <DTACCTUP>
        # dtacctup = sonrs[4]
        # self.element(dtacctup, tag='DTACCTUP', data='20031029101003')

        # # <SIGNONMSGSRSV1> - <SONRS> - <FI>
        # fi = sonrs[5]
        # self.aggregate(fi, tag='FI', num_children=2)

        # # <SIGNONMSGSRSV1> - <SONRS> - <FI> - <ORG>
        # org = fi[0]
        # self.element(org, tag='ORG', data='NCH')

        # # <SIGNONMSGSRSV1> - <SONRS> - <FI> - <FID>
        # fid = fi[1]
        # self.element(fid , tag='FID', data='1001')

        # # <BANKMSGSRSV1>
        # bankmsgs = ofx[1]
        # self.aggregate(bankmsgs, tag='BANKMSGSRSV1', num_children=1)

        # # <BANKMSGSRSV1> - <STMTTRNRS>
        # stmttrnrs = bankmsgs[0]
        # self.aggregate(stmttrnrs, tag='STMTTRNRS', num_children=3)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <TRNUID>
        # trnuid = stmttrnrs[0]
        # self.element(trnuid, tag='TRNUID', data='1001')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STATUS>
        # status = stmttrnrs[1]
        # self.aggregate(status, tag='STATUS', num_children=2)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STATUS> - <CODE>
        # code = status[0]
        # self.element(code, tag='CODE', data='0')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STATUS> - <SEVERITY>
        # severity = status[1]
        # self.element(severity, tag='SEVERITY', data='INFO')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS>
        # stmtrs = stmttrnrs[2]
        # self.aggregate(stmtrs, tag='STMTRS', num_children=5)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <CURDEF>
        # curdef = stmtrs[0]
        # self.element(curdef, tag='CURDEF', data='USD')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKACCTFROM>
        # bankacctfrom = stmtrs[1]
        # self.aggregate(bankacctfrom, tag='BANKACCTFROM', num_children=3)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKACCTFROM> - <BANKID>
        # bankid = bankacctfrom[0]
        # self.element(bankid, tag='BANKID', data='121099999')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKACCTFROM> - <ACCTID>
        # acctid = bankacctfrom[1]
        # self.element(acctid, tag='ACCTID', data='999988')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKACCTFROM> - <ACCTTYPE>
        # accttype = bankacctfrom[2]
        # self.element(accttype, tag='ACCTTYPE', data='CHECKING')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST>
        # banktranlist = stmtrs[2]
        # self.aggregate(banktranlist, tag='BANKTRANLIST', num_children=4)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <DTSTART>
        # dtstart = banktranlist[0]
        # self.element(dtstart, tag='DTSTART', data='20051001')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <DTEND>
        # dtend = banktranlist[1]
        # self.element(dtend, tag='DTEND', data='20051028')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #1
        # stmttrn1 = banktranlist[2]
        # self.aggregate(stmttrn1, tag='STMTTRN', num_children=5)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #1 - <TRNTYPE>
        # trntype = stmttrn1[0]
        # self.element(trntype, tag='TRNTYPE', data='CHECK')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #1 - <DTPOSTED>
        # dtposted = stmttrn1[1]
        # self.element(dtposted, tag='DTPOSTED', data='20051004')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #1 - <TRNAMT>
        # trnamt = stmttrn1[2]
        # self.element(trnamt, tag='TRNAMT', data='-200.00')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #1 - <FITID>
        # fitid = stmttrn1[3]
        # self.element(fitid, tag='FITID', data='00002')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #1 - <CHECKNUM>
        # checknum = stmttrn1[4]
        # self.element(checknum, tag='CHECKNUM', data='1000')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #2
        # stmttrn2 = banktranlist[3]
        # self.aggregate(stmttrn2, tag='STMTTRN', num_children=5)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #2 - <TRNTYPE>
        # trntype = stmttrn2[0]
        # self.element(trntype, tag='TRNTYPE', data='ATM')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #2 - <DTPOSTED>
        # dtposted = stmttrn2[1]
        # self.element(dtposted, tag='DTPOSTED', data='20051020')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #2 - <DTUSER>
        # dtuser = stmttrn2[2]
        # self.element(dtuser, tag='DTUSER', data='20051020')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #2 - <TRNAMT>
        # trnamt = stmttrn2[3]
        # self.element(trnamt, tag='TRNAMT', data='-300.00')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <BANKTRANLIST> - <STMTTRN> #2 - <FITID>
        # fitid = stmttrn2[4]
        # self.element(fitid, tag='FITID', data='00003')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <LEDGERBAL>
        # ledgerbal = stmtrs[3]
        # self.aggregate(ledgerbal, tag='LEDGERBAL', num_children=2)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <LEDGERBAL> - <BALAMT>
        # balamt = ledgerbal[0]
        # self.element(balamt, tag='BALAMT', data='200.29')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <LEDGERBAL> - <DTASOF>
        # dtasof = ledgerbal[1]
        # self.element(dtasof, tag='DTASOF', data='200510291120')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <AVAILBAL>
        # availbal = stmtrs[4]
        # self.aggregate(availbal, tag='AVAILBAL', num_children=2)

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <AVAILBAL> - <BALAMT>
        # balamt = availbal[0]
        # self.element(balamt, tag='BALAMT', data='200.29')

        # # <BANKMSGSRSV1> - <STMTTRNRS> - <STMTRS> - <AVAILBAL> - <DTASOF>
        # dtasof = availbal[1]
        # self.element(dtasof, tag='DTASOF', data='200510291120')

    # def test_flatten(self):
        # sonrs = Aggregate._flatten(ofx[0][0])
        # self.assertEqual(sonrs, {'code': '0', 'severity': 'INFO',
                                 # 'dtserver': '20051029101003',
                                 # 'language': 'ENG',
                                 # 'dtprofup': '19991029101003',
                                 # 'dtacctup': '20031029101003',
                                 # 'org': 'NCH', 'fid': '1001'})

        # stmttrnrs = ofx[1][0]
        # stmttrnrs_status = Aggregate._flatten(stmttrnrs[1])
        # self.assertEqual(stmttrnrs_status, {'code': '0', 'severity': 'INFO'})

        # stmtrs = stmttrnrs[2]
        # acctfrom = Aggregate._flatten(stmtrs[1])
        # self.assertEqual(acctfrom, {'bankid': '121099999', 'acctid': '999988',
                                    # 'accttype': 'CHECKING'})
        # tranlist = stmtrs[2]
        # stmttrn1 = Aggregate._flatten(tranlist[2])
        # self.assertEqual(stmttrn1, {'trntype': 'CHECK', 'dtposted': '20051004',
                                    # 'trnamt': '-200.00', 'fitid': '00002',
                                    # 'checknum': '1000'})
        # stmttrn2 = Aggregate._flatten(tranlist[3])
        # self.assertEqual(stmttrn2, {'trntype': 'ATM', 'dtposted': '20051020',
                                    # 'dtuser': '20051020', 'trnamt': '-300.00',
                                    # 'fitid': '00003'})
        # ledgerbal = Aggregate._flatten(stmtrs[3])
        # self.assertEqual(ledgerbal, {'balamt': '200.29',
                                     # 'dtasof': '200510291120'})
        # availbal = Aggregate._flatten(stmtrs[4])
        # self.assertEqual(availbal, {'balamt': '200.29',
                                    # 'dtasof': '200510291120'})


if __name__ == '__main__':
    unittest.main()
