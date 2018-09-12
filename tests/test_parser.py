# coding: utf-8

# stdlib imports
import unittest
from unittest import (
    TestCase,
)
try:
    from unittest.mock import (
        MagicMock,
        call,
        patch,
        sentinel,
    )
    import builtins
except ImportError:
    # Python 2 depends on external mock package
    from mock import (
        MagicMock,
        call,
        patch,
        sentinel,
    )
    import __builtin__ as builtins

from xml.etree.ElementTree import (
    Element,
)
from io import BytesIO
from tempfile import (
    TemporaryFile,
    NamedTemporaryFile,
)


# local imports
from ofxtools.Parser import (
    OFXTree,
    TreeBuilder,
    ParseError,
)
from ofxtools.header import OFXHeader


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
        """ Call regex.match() on input string; return match groups """
        m = self.regex.match(markup)
        self.assertIsNotNone(m)
        groupdict = m.groupdict()
        self.assertEqual(len(groupdict), 4)
        return (groupdict['tag'], groupdict['text'], groupdict['closetag'])

    def test_sgml_tag(self):
        markup = "<TAG>data"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ('TAG', 'data', None))

    def test_sgml_endtag(self):
        markup = "</TAG>data"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ('/TAG', 'data', None))

    def test_xml_tag(self):
        markup = "<TAG>data</TAG>"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ('TAG', 'data', 'TAG'))

    def test_xml_mismatched_endtag(self):
        markup = "<TAG>data</GAT>"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ('TAG', 'data', None))

    def test_xml_selfclosing_tag(self):
        markup = "<TAG />"
        parsed = self._parsetag(markup)
        self.assertEqual(parsed, ('TAG /', None, None))

    def test_finditer_sgml(self):
        markup = "<TAG1><TAG2>value"
        self.builder.feed(markup)
        expected = [call('TAG1', None, None), call('TAG2', 'value', None)]
        self.assertEqual(self.builder._feedmatch.mock_calls, expected)

    def test_finditer_xml(self):
        markup = "<TAG1><TAG2>value</TAG2></TAG1>"
        self.builder.feed(markup)
        expected = [call('TAG1', None, None),
                    call('TAG2', 'value', 'TAG2'),
                    call('/TAG1', None, None)]
        self.assertEqual(self.builder._feedmatch.mock_calls, expected)


class TreeBuilderTestCase(TestCase):
    """ """
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
        self.assertEqual(None, groom(''))
        self.assertEqual(None, groom('   \n'))
        self.assertEqual('text', groom('text   \n'))
        self.assertEqual('text', groom('   \ntext'))

    def test_start_agg(self):
        (tag, text, closetag) = ('TAG', None, None)
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with('TAG', {})
        self.builder.data.assert_not_called()
        self.builder.end.assert_not_called()

    def test_empty_aggV2(self):
        (tag, text, closetag) = ('TAG', None, 'TAG')
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with('TAG', {})
        self.builder.data.assert_not_called()
        self.builder.end.assert_called_once_with('TAG')

    def test_elemV1(self):
        (tag, text, closetag) = ('TAG', 'value', None)
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with('TAG', {})
        self.builder.data.assert_called_once_with('value')
        self.builder.end.assert_called_once_with('TAG')

    def test_elemV2(self):
        (tag, text, closetag) = ('TAG', 'value', 'TAG')
        self.builder._start(tag, text, closetag)
        self.builder.start.assert_called_once_with('TAG', {})
        self.builder.data.assert_called_once_with('value')
        self.builder.end.assert_called_once_with('TAG')

    def test_feedmatch_empty_tag(self):
        (tag, text, closetag) = (None, 'value', 'TAG')
        with self.assertRaises(AssertionError):
            self.builder._feedmatch(tag, text, closetag)

    def test_feedmatch_tag_mismatch(self):
        (tag, text, closetag) = ('TAG', 'value', 'GAT')
        with self.assertRaises(AssertionError):
            self.builder._feedmatch(tag, text, closetag)

    def test_feedmatch_start(self):
        self.builder._start = MagicMock()
        (tag, text, closetag) = ('TAG', 'value', 'TAG')
        self.builder._feedmatch(tag, text, closetag)
        self.builder._start.assert_called_once_with('TAG', 'value', 'TAG')
        self.builder.end.assert_not_called()

    def test_feedmatch_end(self):
        self.builder._start = MagicMock()
        (tag, text, closetag) = ('/TAG', None, None)
        self.builder._feedmatch(tag, text, closetag)
        self.builder._start.assert_not_called()
        self.builder.end.assert_called_once_with('TAG')

    def test_feedmatch_end_tail(self):
        (tag, text, closetag) = ('/TAG', 'value', None)
        with self.assertRaises(ParseError):
            self.builder._feedmatch(tag, text, closetag)

    def test_feedmatch_tag_mismatch(self):
        self.builder._start = MagicMock()
        self.builder._end = MagicMock()
        (tag, text, closetag) = ('TAG', 'value', 'GAT')
        with self.assertRaises(AssertionError):
            self.builder._feedmatch(tag, text, closetag)

    def test_close_tail(self):
        data = "</FOO>illegal"
        # self.builder.feed(data)
        with self.assertRaises(ParseError):
            self.builder.feed(data)

    def test_open_tail(self):
        data = "<FOO>bar</FOO>illegal"
        # self.builder.feed(data)
        with self.assertRaises(ParseError):
            self.builder.feed(data)


class OFXTreeTestCase(TestCase):
    """ """
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

        source = '/path/to/file.ofx'
        self.tree.parse(source, parser=mockTreeBuilderClass)
        self.tree._read.assert_called_once_with(source)
        mockTreeBuilderInstance.feed.assert_called_once_with(sentinel.ofx)
        mockTreeBuilderInstance.close.assert_called_once()
        self.assertEqual(self.tree._root, sentinel.root)

    def test_read_filename(self):
        OFXHeader.parse = MagicMock()
        fake_header = sentinel.header
        fake_body = sentinel.ofx
        OFXHeader.parse.return_value = (fake_header, fake_body)

        with patch('builtins.open') as fake_open:
            fake_open.return_value = sentinel.file

            source = NamedTemporaryFile()
            source.write(b'a bunch of text')
            source.seek(0)

            output = self.tree._read(source.name)
            source.close()
            fake_open.assert_called_once_with(source.name, 'rb')
            OFXHeader.parse.assert_called_once_with(sentinel.file)
            self.assertEqual(output, (fake_header, fake_body))

    def test_read_file(self):
        OFXHeader.parse = MagicMock()
        fake_header = sentinel.header
        fake_body = sentinel.ofx
        OFXHeader.parse.return_value = (fake_header, fake_body)

        with patch('builtins.open') as fake_open:
            fake_open.return_value = sentinel.file

            source = NamedTemporaryFile()
            source.write(b'a bunch of text')
            source.seek(0)

            output = self.tree._read(source)
            source.close()
            fake_open.assert_not_called()
            OFXHeader.parse.assert_called_once_with(source)
            self.assertEqual(output, (fake_header, fake_body))

    def test_read_illegal(self):
        source = 'a bunch of text'
        with self.assertRaises(ParseError):
            self.tree._read(source)

    def test_convert(self):
        # Fake the result of OFXTree.parse()
        self.tree._root = Element('FAKE')

        # OFXTree.convert() returns an OFX instance constructed from its root
        with patch('ofxtools.Parser.Aggregate') as MockAggregate:
            ofx = self.tree.convert()
            MockAggregate.from_etree.assert_called_once_with(self.tree._root)
            self.assertEqual(ofx, MockAggregate.from_etree())
            
    def test_convert_unparsed(self):
        # Calling OFXTree.convert() without first calling OFXTree.parse()
        # raises ValueError
        with self.assertRaises(ValueError):
            self.tree.convert()


if __name__ == '__main__':
    unittest.main()
