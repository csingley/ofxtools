#!/usr/bin/env python
import sys
import os
import re
import xml.etree.ElementTree as ET
from sgmllib import SGMLParser
from decimal import Decimal

from utilities import _, OFXv1, OFXv2, prettify

if sys.version_info < (2, 7):
    raise RuntimeError('ofx.parser library requires Python v2.7+')


#class OFXSGMLTreeBuilder(ET.TreeBuilder):
    #""" """
    #def start(self, tag):
        ## First clean up any dangling unclosed leaf nodes
        #if self._data:
            #ET.TreeBuilder.end(self, self._last.tag)
        #ET.TreeBuilder.start(self, tag, attrs={})

    #def end(self, tag):
        ## If I see a closing tag different than the top of the stack, then
        ## the unclosed tag must be a data-bearing leaf node, and the closing
        ## tag is that of its containing parent aggregate.
        ## First close the data-bearing element, then proceed as usual
        #toptag = self._elem[-1].tag
        #if tag != toptag:
            #ET.TreeBuilder.end(self, toptag)
        #ET.TreeBuilder.end(self, tag)


#class OFXSGMLParser(SGMLParser):
    #"""
    #Parses OFX v1&v2 data files into an ElementTree instance.
    #Accessible via standard feed/close consumer interface.

    #Built on sgmllib, which is deprecated and going away in py3k.
    #"""

    #def __init__(self):
        #self.__builder = OFXSGMLTreeBuilder()
        #SGMLParser.__init__(self)

    #def reset(self):
        #self.header = None
        #self.tree = ET.ElementTree()
        #SGMLParser.reset(self)

    #def close(self):
        #root = self.__builder.close()
        #SGMLParser.close(self)
        #return root

    #def unknown_starttag(self, tag, attrib):
        #tag = tag.upper()
        ##OFX tags don't have attributes
        #self.__builder.start(tag)

    #def unknown_endtag(self, tag):
        #tag = tag.upper()
        #self.__builder.end(tag)

    #def handle_data(self, text):
        ## FIXME - Find a better way of stripping whitespace.
        ## If SGMLParser sees a data with (e.g.) an ampersand character in it,
        ## the regexes break up the data in chunks, and those chunks can
        ## have their whitespace stripped inappropriately, so desirable
        ## whitespace ends up missing from the data.
        ## e.g. "Peanut butter & jelly" -> "Peanut butter&jelly".
        ## However, the attempted fix below blows up the parser.
        ## The impact on OFX data quality is minimal (basically just
        ## securities names), but still, look into this.
        ##text = text.strip('\f\n\r\t\v') # Strip whitespace, except space char
        #text = text.strip(' \f\n\r\t\v')
        #if text:
            #self.__builder.data(text)


class OFXParser(ET.ElementTree):
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
                            """, re.VERBOSE)

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
                            \?>\s+""", re.VERBOSE)

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source, 'rb')
        source = source.read()

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
            #parser = OFXSGMLParser()
            parser = OFXTreeBuilder()
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
            parser = ET.XMLTreeBuilder()

        ### Then parse tag soup
        parser.feed(source)
        self._root = parser.close()
        return self._root


class OFXTreeBuilder(ET.TreeBuilder):
    """ """
    regex = re.compile(r"""<(?P<TAG>[A-Z1-9./]+?)>
                            (?P<TEXT>[^<]+)?
                            (</(?P=TAG)>)?
                            \s*""", re.VERBOSE)

    def feed(self, data):
        for match in self.regex.finditer(data):
            tag, text, closingTag = match.groups()
            text = text or '' # None has no strip() method
            text = text.strip()
            if len(text):
                # OFX "element" (i.e. data-bearing leaf)
                assert not tag.startswith('/')
                self.start(tag, attrs={})
                self.data(text)
                # Closing tags are optional for OFXv1 data elements
                # Close them all, whether or not they're explicitly closed
                self.end(tag)
            else:
                # OFX "aggregate" (tagged branch w/ no data)
                if tag.startswith('/'):
                    # aggregate closing tag
                    assert not text
                    self.end(tag[1:])
                else:
                    # aggregate opening tag
                    self.start(tag, attrs={})
                    if closingTag:
                        # regex captures the entire closing tag
                        # validate that closing/opening tags match
                        assert closingTag.replace(tag, '') == '</>'
                        self.end(tag)


def main():
    from argparse import ArgumentParser
    argparser = ArgumentParser()
    argparser.add_argument('file')
    args = argparser.parse_args()

    ofxparser = OFXParser()
    root = ofxparser.parse(_(args.file))
    #root = ofxparser.getroot()
    print prettify(ET.tostring(root))


if __name__ == '__main__':
    main()
