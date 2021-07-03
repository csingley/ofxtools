# coding: utf-8
""" Unit tests for ofxtools.Parser """

# stdlib imports
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, call, patch, sentinel
from xml.etree.ElementTree import Element
from io import BytesIO, StringIO
from tempfile import NamedTemporaryFile


# local imports
from ofxtools.Parser import OFXTree, TreeBuilder, ParseError, main


class TreeBuilderRegexTestCase(TestCase):
    """ """

    def setUp(self):
        self.builder = TreeBuilder()
        self.builder._feedmatch = MagicMock()
        self.regex = self.builder.regex

    def tearDown(self):
        del self.regex
        del self.builder

    def _parsetag(self, markup):
        """Call regex.match() on input string; return match groups"""
        m = self.regex.match(markup)
        self.assertIsNotNone(m)
        groupdict = m.groupdict()
        self.assertEqual(len(groupdict), 4)
        return (groupdict["tag"], groupdict["text"], groupdict["closetag"])

    def test_sgml_tag(self):
        markup = "<TAG>data"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ("TAG", "data", None))

    def test_sgml_endtag(self):
        markup = "</TAG>data"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ("/TAG", "data", None))

    def test_xml_tag(self):
        markup = "<TAG>data</TAG>"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ("TAG", "data", "TAG"))

    def test_xml_mismatched_endtag(self):
        markup = "<TAG>data</GAT>"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ("TAG", "data", None))

    def test_xml_selfclosing_tag(self):
        markup = "<TAG />"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ("TAG /", None, None))

    def test_finditer_sgml(self):
        markup = "<TAG1><TAG2>value"
        self.builder.feed(markup)
        expected = [call("TAG1", None, None), call("TAG2", "value", None)]
        self.assertEqual(self.builder._feedmatch.mock_calls, expected)

    def test_finditer_xml(self):
        markup = "<TAG1><TAG2>value</TAG2></TAG1>"
        self.builder.feed(markup)
        expected = [
            call("TAG1", None, None),
            call("TAG2", "value", "TAG2"),
            call("/TAG1", None, None),
        ]
        self.assertEqual(self.builder._feedmatch.mock_calls, expected)


class TreeBuilderUnitTestCase(TestCase):
    """Unit tests for ofxtools.Parser.Treebuilder"""

    def setUp(self):
        builder = TreeBuilder()
        builder.start = MagicMock()
        builder.data = MagicMock()
        builder.end = MagicMock()

        self.builder = builder

    def tearDown(self):
        del self.builder

    def test_groomstring(self):
        groom = self.builder._groomstring
        self.assertEqual(None, groom(None))
        self.assertEqual(None, groom(""))
        self.assertEqual(None, groom("   \n"))
        self.assertEqual("text", groom("text   \n"))
        self.assertEqual("text", groom("   \ntext"))

    def test_start_agg(self):
        (tag, text, closetag) = ("TAG", None, None)
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with("TAG", {})
        self.builder.data.assert_not_called()
        self.builder.end.assert_not_called()

    def test_empty_aggV2(self):
        (tag, text, closetag) = ("TAG", None, "TAG")
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with("TAG", {})
        self.builder.data.assert_not_called()
        self.builder.end.assert_called_once_with("TAG")

    def test_elemV1(self):
        (tag, text, closetag) = ("TAG", "value", None)
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with("TAG", {})
        self.builder.data.assert_called_once_with("value")
        self.builder.end.assert_called_once_with("TAG")

    def test_elemV2(self):
        (tag, text, closetag) = ("TAG", "value", "TAG")
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with("TAG", {})
        self.builder.data.assert_called_once_with("value")
        self.builder.end.assert_called_once_with("TAG")

    def test_feedmatch_empty_tag(self):
        (tag, text, closetag) = (None, "value", "TAG")
        with self.assertRaises(AssertionError):
            self.builder._feedmatch(tag, text, closetag)

    def test_feedmatch_tag_mismatch(self):
        (tag, text, closetag) = ("TAG", "value", "GAT")
        with self.assertRaises(AssertionError):
            self.builder._feedmatch(tag, text, closetag)

    def test_feedmatch_start(self):
        self.builder._start = MagicMock()
        (tag, text, closetag) = ("TAG", "value", "TAG")
        self.builder._feedmatch(tag, text, closetag)
        self.builder._start.assert_called_once_with("TAG", "value", "TAG")
        self.builder.end.assert_not_called()

    def test_feedmatch_end(self):
        self.builder._start = MagicMock()
        (tag, text, closetag) = ("/TAG", None, None)
        self.builder._feedmatch(tag, text, closetag)
        self.builder._start.assert_not_called()
        self.builder.end.assert_called_once_with("TAG")

    def test_feedmatch_end_tail(self):
        (tag, text, closetag) = ("/TAG", "value", None)
        with self.assertRaises(ParseError):
            self.builder._feedmatch(tag, text, closetag)

    def test_close_tail(self):
        data = "</FOO>illegal"
        with self.assertRaises(ParseError):
            self.builder.feed(data)

    def test_open_tail(self):
        data = "<FOO>bar</FOO>illegal"
        with self.assertRaises(ParseError):
            self.builder.feed(data)


class TreeBuilderUnitFunctionalTestCase(TestCase):
    """Functional tests for ofxtools.Parser.Treebuilder"""

    def _testElement(self, element, tag, text, length):
        self.assertIsInstance(element, Element)
        self.assertEqual(element.tag, tag)
        self.assertEqual(element.text, text)
        self.assertEqual(len(element), length)

    def _testFeedSonrs(self, body):
        """
        str -> Element tests reused to test responses with identical content
        but different formatting.
        """
        builder = TreeBuilder()
        builder.feed(body)
        root = builder.close()

        self._testElement(root, tag="OFX", text=None, length=1)

        msgsrs = root[0]
        self._testElement(msgsrs, tag="SIGNONMSGSRSV1", text=None, length=1)

        sonrs = msgsrs[0]
        self._testElement(sonrs, tag="SONRS", text=None, length=6)

        status, dtserver, language, dtprofup, dtacctup, fi = sonrs

        self._testElement(status, tag="STATUS", text=None, length=2)

        code, severity = status

        self._testElement(code, tag="CODE", text="0", length=0)
        self._testElement(severity, tag="SEVERITY", text="INFO", length=0)

        self._testElement(dtserver, tag="DTSERVER", text="20051029101003", length=0)
        self._testElement(language, tag="LANGUAGE", text="ENG", length=0)
        self._testElement(dtprofup, tag="DTPROFUP", text="19991029101003", length=0)
        self._testElement(dtacctup, tag="DTACCTUP", text="20031029101003", length=0)
        self._testElement(fi, tag="FI", text=None, length=2)

        org, fid = fi

        self._testElement(org, tag="ORG", text="NCH", length=0)
        self._testElement(fid, tag="FID", text="1001", length=0)

    def testFeedClosedTagsWhitespace(self):
        """
        TreeBuilder.feed() correctly parses soup with closing tags,
        interspersed whitepace.
        """
        body = """
        <OFX>
            <SIGNONMSGSRSV1>
                <SONRS>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <DTSERVER>20051029101003</DTSERVER>
                    <LANGUAGE>ENG</LANGUAGE>
                    <DTPROFUP>19991029101003</DTPROFUP>
                    <DTACCTUP>20031029101003</DTACCTUP>
                    <FI>
                        <ORG>NCH</ORG>
                        <FID>1001</FID>
                    </FI>
                </SONRS>
            </SIGNONMSGSRSV1>
        </OFX>
        """
        self._testFeedSonrs(body)

    def testFeedUnclosedTagsWhitespace(self):
        """
        TreeBuilder.feed() correctly parses soup with no closing element tags,
        interspersed whitepace.
        """
        body = """
        <OFX>
        \t<SIGNONMSGSRSV1>
        \t\t<SONRS>
        \t\t\t<STATUS>
        \t\t\t\t<CODE>0
        \t\t\t\t<SEVERITY>INFO
        \t\t\t</STATUS>
        \t\t\t<DTSERVER>20051029101003
        \t\t\t<LANGUAGE>ENG
        \t\t\t<DTPROFUP>19991029101003
        \t\t\t<DTACCTUP>20031029101003
        \t\t\t<FI>
        \t\t\t\t<ORG>NCH
        \t\t\t\t<FID>1001
        \t\t\t</FI>
        \t\t</SONRS>
        \t</SIGNONMSGSRSV1>
        </OFX>
        """
        self._testFeedSonrs(body)

    def testFeedClosedTagsNoWhitespace(self):
        """
        TreeBuilder.feed() correctly parses soup with closing tags,
        no interspersed whitepace.
        """
        body = (
            "<OFX>"
            "<SIGNONMSGSRSV1>"
            "<SONRS>"
            "<STATUS>"
            "<CODE>0</CODE>"
            "<SEVERITY>INFO</SEVERITY>"
            "</STATUS>"
            "<DTSERVER>20051029101003</DTSERVER>"
            "<LANGUAGE>ENG</LANGUAGE>"
            "<DTPROFUP>19991029101003</DTPROFUP>"
            "<DTACCTUP>20031029101003</DTACCTUP>"
            "<FI>"
            "<ORG>NCH</ORG>"
            "<FID>1001</FID>"
            "</FI>"
            "</SONRS>"
            "</SIGNONMSGSRSV1>"
            "</OFX>"
        )
        self._testFeedSonrs(body)

    def testFeedUnclosedTagsNoWhitespace(self):
        """
        TreeBuilder.feed() correctly parses soup with no closing element tags,
        no interspersed whitepace.
        """
        body = (
            "<OFX>"
            "<SIGNONMSGSRSV1>"
            "<SONRS>"
            "<STATUS>"
            "<CODE>0"
            "<SEVERITY>INFO"
            "</STATUS>"
            "<DTSERVER>20051029101003"
            "<LANGUAGE>ENG"
            "<DTPROFUP>19991029101003"
            "<DTACCTUP>20031029101003"
            "<FI>"
            "<ORG>NCH"
            "<FID>1001"
            "</FI>"
            "</SONRS>"
            "</SIGNONMSGSRSV1>"
            "</OFX>"
        )
        self._testFeedSonrs(body)


class OFXTreeTestCase(TestCase):
    def setUp(self):
        self.tree = OFXTree()

    def tearDown(self):
        del self.tree

    def test_parse(self):
        # OFXTree.parse() reads the source, strips the OFX header, feed()s
        # the OFX data to TreeBuilder, and stores the return value from
        # TreeBuilder.close() as its _root
        self.tree._read = MagicMock()
        self.tree._read.return_value = (sentinel.header, sentinel.ofx)

        mockTreeBuilderClass = MagicMock()
        mockTreeBuilderInstance = mockTreeBuilderClass.return_value
        mockTreeBuilderInstance.close.return_value = sentinel.root

        source = "/path/to/file.ofx"
        self.tree.parse(source, parser=mockTreeBuilderInstance)
        self.tree._read.assert_called_once_with(source)
        mockTreeBuilderInstance.feed.assert_called_once_with(sentinel.ofx)
        # FIXME - Fails on Python 3.5 ???
        #  mockTreeBuilderInstance.close.assert_called_once()
        self.assertEqual(self.tree._root, sentinel.root)

    def test_read_filename(self):
        with patch("builtins.open") as fake_open:
            with patch("ofxtools.Parser.parse_header") as fake_parse_header:
                fake_open.return_value = sentinel.file

                fake_header = sentinel.header
                fake_body = sentinel.ofx
                fake_parse_header.return_value = (fake_header, fake_body)

                source = NamedTemporaryFile()
                source.write(b"a bunch of text")
                source.seek(0)

                output = self.tree._read(source.name)
                source.close()
                fake_open.assert_called_once_with(source.name, "rb")
                fake_parse_header.assert_called_once_with(sentinel.file)
                self.assertEqual(output, (fake_header, fake_body))

    def test_read_file(self):
        with patch("ofxtools.Parser.parse_header") as fake_parse_header:
            fake_header = sentinel.header
            fake_body = sentinel.ofx
            fake_parse_header.return_value = (fake_header, fake_body)

            source = NamedTemporaryFile()
            source.write(b"a bunch of text")
            source.seek(0)

            output = self.tree._read(source)
            source.close()
            fake_parse_header.assert_called_once_with(source)
            self.assertEqual(output, (fake_header, fake_body))

    def test_read_not_bytes(self):
        source = NamedTemporaryFile(mode="w+")
        source.write("a bunch of text")
        source.seek(0)

        with self.assertRaises(ValueError):
            self.tree._read(source)

    def test_read_byteslike(self):
        # PR #15
        with patch("ofxtools.Parser.parse_header") as fake_parse_header:
            fake_header = sentinel.header
            fake_body = sentinel.ofx
            fake_parse_header.return_value = (fake_header, fake_body)

            source = BytesIO(b"a bunch of text")
            source.seek(0)

            output = self.tree._read(source)
            source.close()
            fake_parse_header.assert_called_once_with(source)
            self.assertEqual(output, (fake_header, fake_body))

    def test_read_illegal(self):
        source = "a bunch of text"
        with self.assertRaises(FileNotFoundError):
            self.tree._read(source)

    def test_convert(self):
        # Fake the result of OFXTree.parse()
        self.tree._root = Element("FAKE")

        # OFXTree.convert() returns an OFX instance constructed from its root
        with patch("ofxtools.Parser.Aggregate") as MockAggregate:
            ofx = self.tree.convert()
            MockAggregate.from_etree.assert_called_once_with(self.tree._root)
            self.assertEqual(ofx, MockAggregate.from_etree())

    def test_convert_unparsed(self):
        # Calling OFXTree.convert() without first calling OFXTree.parse()
        # raises ValueError
        with self.assertRaises(ValueError):
            self.tree.convert()


class MainTestCase(TestCase):
    """Test main()"""

    def testMain(self):
        import os

        this_dir = os.path.dirname(os.path.abspath(__file__))
        source = os.path.join(this_dir, "data", "invstmtrs.ofx")

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            main(source)
            output = stdout.getvalue()
            self.assertEqual(
                output,
                (
                    "["
                    "<BUYSTOCK(invbuy=<INVBUY(invtran=<INVTRAN(fitid='23321', dttrade=datetime.datetime(2005, 8, 25, 0, 0, tzinfo=<UTC>), dtsettle=datetime.datetime(2005, 8, 28, 0, 0, tzinfo=<UTC>))>, secid=<SECID(uniqueid='123456789', uniqueidtype='CUSIP')>, units=Decimal('100'), unitprice=Decimal('50.00'), commission=Decimal('25.00'), total=Decimal('-5025.00'), subacctsec='CASH', subacctfund='CASH')>, buytype='BUY')>"
                    ", "
                    "<INVBANKTRAN(stmttrn=<STMTTRN(trntype='CREDIT', dtposted=datetime.datetime(2005, 8, 25, 0, 0, tzinfo=<UTC>), dtuser=datetime.datetime(2005, 8, 25, 0, 0, tzinfo=<UTC>), trnamt=Decimal('1000.00'), fitid='12345', name='Customer deposit', memo='Your check #1034')>, subacctfund='CASH')>"
                    "]\n"
                ),
            )


if __name__ == "__main__":
    unittest.main()
