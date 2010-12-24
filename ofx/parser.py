#!/usr/bin/env python
import sys
import os
import re
import xml.etree.ElementTree as ET
from sgmllib import SGMLParser
from decimal import Decimal

from utilities import _, OFXv1, OFXv2, prettify

if sys.version_info[:2] != (2, 7):
    raise RuntimeError('ofx.parser library requires Python v2.7')

HEADER_FIELDS = {'100': ('DATA', 'VERSION', 'SECURITY', 'ENCODING', 'CHARSET',
                        'COMPRESSION', 'OLDFILEUID', 'NEWFILEUID'),}


class OFXTreeBuilder(ET.TreeBuilder):
    """
    OFX doesn't close tags on leaf node elements.  SGMLParser is stateless, so
    it can't handle OFX's implicitly-closed tags.  Rather than reimplementing
    that state at the parser level, or have OFXParser look up TreeBuilder's
    skirt at its private attributes, it's better just to accept the breach of
    orthogonality and delegate the handling of implicit tag closure to
    TreeBuilder, who is already maintaining all the necessary state.

    So that's how the OFXParser and OFXTreeBuilder subclasses work together.
    """
    def start(self, tag):
        # First clean up any dangling unclosed leaf nodes
        if self._data:
            self._flush()
            self._last = self._elem.pop()
            self._tail = 1
        ET.TreeBuilder.start(self, tag, attrs={})

    def data(self, data):
        ET.TreeBuilder.data(self, data)

    def end(self, tag):
        # First clean up any dangling unclosed leaf nodes
        if self._data:
            self._flush()
            self._last = self._elem.pop()
            self._tail = 1
        ET.TreeBuilder.end(self, tag)


class OFXParser(SGMLParser):
    """
    Parses OFX v1&v2 data files into an ElementTree instance.
    Accessible via standard feed/close consumer interface.

    Built on sgmllib, which is deprecated and going away in py3k.
    """
    v1Header = re.compile(r"""\s*
                            OFXHEADER:(?P<OFXHEADER>\d+)\s+
                            DATA:(?P<DATA>[A-Z]+)\s+
                            VERSION:(?P<VERSION>\d+)\s+
                            SECURITY:(?P<SECURITY>[A-Z]+)\s+
                            ENCODING:(?P<ENCODING>[A-Z]+)\s+
                            CHARSET:(?P<CHARSET>\d+)\s+
                            COMPRESSION:(?P<COMPRESSION>[A-Z]+)\s+
                            OLDFILEUID:(?P<OLDFILEUID>[\w-]+)\s+
                            NEWFILEUID:(?P<NEWFILEUID>[\w-]+)\s+
                            """, re.X)

    v2Header = re.compile(r"""(<\?xml\s+
                            (version=\"(?P<XMLVERSION>[\d.]+)\")?\s*
                            (encoding=\"(?P<ENCODING>[\w-]+)\")?\s*
                            (standalone=\"(?P<STANDALONE>[\w]+)\")?\s*
                            \?>)\s*
                            <\?OFX\s+
                            OFXHEADER=\"(?P<OFXHEADER>\d+)\"\s+
                            VERSION=\"(?P<VERSION>\d+)\"\s+
                            SECURITY=\"(?P<SECURITY>[A-Z]+)\"\s+
                            OLDFILEUID=\"(?P<OLDFILEUID>[\w-]+)\"\s+
                            NEWFILEUID=\"(?P<NEWFILEUID>[\w-]+)\"\s*
                            \?>\s+""", re.X)

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.__builder = OFXTreeBuilder()
        SGMLParser.__init__(self)

    def reset(self):
        self.header = None
        self.tree = ET.ElementTree()
        SGMLParser.reset(self)

    def close(self):
        root = self.__builder.close()
        SGMLParser.close(self)
        return root

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source, 'rb')
        source = source.read().strip()
        ### First parse OFX header
        v1Header = self.v1Header.match(source)
        if v1Header:
            # OFXv1
            header = v1Header.groupdict()
            # Sanity check
            try:
                assert header['OFXHEADER'] == '100'
                assert header['DATA'] == 'OFXSGML'
                assert header['VERSION'] in OFXv1
                assert header['SECURITY'] in ('NONE', 'TYPE1')
                assert header['ENCODING'] in ('UNICODE', 'USASCII')
            except AssertionError:
                raise SyntaxError('Malformed OFX header %s' % str(header))
            source = source[v1Header.end():]
            parser = self
        else:
            v2Header = self.v2Header.match(source)
            if not v2Header:
                raise SyntaxError('Missing OFX Header')
            header = v2Header.groupdict()
            # Sanity check
            try:
                assert header['OFXHEADER'] == '200'
                assert header['VERSION'] in OFXv2
                assert header['SECURITY'] in ('NONE', 'TYPE1')
            except AssertionError:
                raise SyntaxError('Malformed OFX header %s' % str(header))
            source = source[v2Header.end():]
            parser = None # Default to ElementTree.XMLParser
        self.header = header
        ### Then parse tag soup
        root = ET.fromstring(source, parser=parser)
        assert root.tag == 'OFX'
        self.tree._setroot(root)
        return root

    def unknown_starttag(self, tag, attrib):
        tag = tag.upper()
        if self.verbose:
            msg = "starttag opening '%s'" % tag
            print msg
        #OFX tags don't have attributes
        self.__builder.start(tag)

    def unknown_endtag(self, tag):
        tag = tag.upper()
        if self.verbose:
            msg = "endtag closing '%s'" % tag
            print msg
        self.__builder.end(tag)

    def handle_data(self, text):
        #text = text.strip('\f\n\r\t\v') # Strip whitespace, except space char
        text = text.strip()
        if text:
            if self.verbose:
                msg = "handle_data adding data '%s'" % text
                print msg
            self.__builder.data(text)


def main():
    from argparse import ArgumentParser
    argparser = ArgumentParser()
    argparser.add_argument('file')
    argparser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Turn on debug output')
    args = argparser.parse_args()

    ofxparser = OFXParser(verbose=args.verbose)
    root = ofxparser.parse(_(args.file))
    print prettify(ET.tostring(root))

if __name__ == '__main__':
    main()
