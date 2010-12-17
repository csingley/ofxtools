#!/usr/bin/env python
import sys
import os
import xml.etree.ElementTree as ET
from sgmllib import SGMLParser
from decimal import Decimal

from utilities import _, OFXv1, OFXv2

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
        self.header, source = self.unwrap(source)
        root = self.tree.parse(source, parser=self)
        assert root.tag == 'OFX'
        return root

    def unwrap(self, source):
        """ Pass in an open file-like object """
        def next_nonempty_line(source):
            FOUND_CONTENT = False
            while not FOUND_CONTENT:
                line = source.readline()
                # Per Python docs, for str.readline(), 'An empty string is
                #  returned only when EOF is encountered immediately.'
                if line == '':
                    raise EOFError("Source is empty")
                line = line.strip()
                if line:
                    FOUND_CONTENT = True
            return line

        def validateOFXv1Header(line, field):
            try:
                key, value = line.split(':')
                assert key == field
            except ValueError:
                # If split() doesn't yield a duple
                raise ValueError("Malformed OFX header '%s'" % line)
            except AssertionError:
                raise ValueError("Expecting OFX header field '%s' not '%s'" % (field, key))
            return key.strip(), value.strip()

        line1 = next_nonempty_line(source)
        if line1.startswith('OFXHEADER'):
            # OFXv1
            # Header is 9 lines of flat text (not markup) that we strip
            header_key, header_version = validateOFXv1Header(line1, 'OFXHEADER')
            header = dict([validateOFXv1Header(source.readline(), f) \
                    for f in HEADER_FIELDS[header_version]])
            header[header_key] = header_version
            # Sanity check
            assert header['DATA'] == 'OFXSGML'
            assert header['VERSION'] in OFXv1
            #if header['VERSION'] not in OFXv1:
            #    print "OFXv1 header claims OFX version is %s" % header['VERSION']
        elif line1.startswith('<?xml'):
            #OFXv2
            # OFX declaration is the next line of content
            ofx_decl = next_nonempty_line(source)
            assert ofx_decl.endswith('?>')
            args = ofx_decl[:-3].split(' ')[1:]
            header = dict([arg.split('=') for arg in args])
            # Sanity check
            assert header['VERSION'] in OFXv2
        else:
            raise ValueError("Malformed OFX header '%s'" % line1)

        return header, source

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
    ofxparser.parse(_(args.file))
    ofxparser.tree.write('test2.ofx')

if __name__ == '__main__':
    main()
