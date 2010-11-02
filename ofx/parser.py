#!/usr/bin/env python
import sys
import os
import xml.etree.cElementTree as ET
from decimal import Decimal

from utilities import OFXv1, OFXv2

HEADER_FIELDS = {'100': ('DATA', 'VERSION', 'SECURITY', 'ENCODING', 'CHARSET',
                        'COMPRESSION', 'OLDFILEUID', 'NEWFILEUID'),}

class OFXParser(object):
    """
    Reads OFX files (v1 & v2), converts to ElementTree, and extracts the
    interesting data to a SQL database.
    """
    def __init__(self, verbose=False, url=None):
        self.reset()
        self.verbose = verbose
        self.url = url

    def reset(self):
        self.header = None
        self.tree = ET.ElementTree()
        self.connection = None

    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source, 'rb')
        self.header, source = self.unwrap(source)
        root = self._parse(source)
        assert root.tag == 'OFX'

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

    def _parse(self, source):
        # Mark the beginning of the tag soup.
        # This is generally not going to be seek(0), because we've
        # already stepped through the OFX header in unwrapOFX().
        beginning = source.tell()
        try:
            # If sgmlop is installed, it's the fastest parser
            # and it will handle OFXv1-style unclosed tags.
            parser = OFXTreeBuilder_sgmlop(verbose=self.verbose)
        except ImportError:
            # expat (Python's bundled XML parser) is compiled C: fast.
            # expat doesn't validate against DTDs; it will work as long
            # as all tags are closed explicitly, which is allowed by
            # OFXv1 and actually done by some FIs.
            parser = ET.XMLParser()
            try:
                root = self.tree.parse(source, parser)
            except SyntaxError:
                # Fall back to SGMLParser (slow, but handles unclosed tags)
                parser = OFXTreeBuilder(verbose=self.verbose)
                # expat already started reading the file; rewind
                source.seek(beginning)
                root = self.tree.parse(source, parser)
        else:
            root = self.tree.parse(source, parser)
        return root


from sgmllib import SGMLParser
class OFXTreeBuilder(SGMLParser):
    """
    Parses OFX v1&v2 into an ElementTree instance.
    Accessible via standard feed/close consumer interface.

    Built on sgmllib, which is deprecated and going away in py3k.
    """
    def __init__(self, verbose=False):
        self.__builder = ET.TreeBuilder()
        SGMLParser.__init__(self)
        self.inside_data = False
        self.latest_starttag = None
        self.verbose = verbose

    def feed(self, data):
        return SGMLParser.feed(self, data)

    def close(self):
        SGMLParser.close(self)
        return self.__builder.close()

    def unknown_starttag(self, tag, attrib):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "starttag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if self.verbose:
            msg = "starttag opening '%s'" % tag
            print msg
        self.__builder.start(tag, attrib)
        self.latest_starttag = tag

    def unknown_endtag(self, tag):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "endtag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if tag != self.latest_starttag:
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
            self.inside_data = True
            self.__builder.data(text)

class OFXTreeBuilder_sgmlop(object):
    """
    Parses OFX v1&v2 into an ElementTree instance.
    Accessible via standard feed/close consumer interface.

    Built on sgmlop, which is deprecated and going away in py3k:
        http://bugs.python.org/issue1772916
    Nevertheless sgmlop is the best parser available, and can be gotten here:
        http://effbot.org/zone/sgmlop-index.htm
    """
    def __init__(self, verbose=False):
        import sgmlop
        self.__builder = ET.TreeBuilder()
        self.__parser = sgmlop.SGMLParser()
        self.__parser.register(self)
        self.inside_data = False
        self.latest_starttag = None
        self.verbose = verbose

    def feed(self, data):
        self.__parser.feed(data)

    def close(self):
        self.__parser.close()
        # "Note that if you use the standard pattern where a parser class holds
        #  a reference to the sgmlop object, and you'll register methods in the
        #  same class, Python may leak resources. To avoid this, you can either
        #  remove the object from the class before you destroy the class instance,
        #  or unregister all methods (by calling register(None)), or both.
        #  Recent versions of sgmlop supports proper garbage collection for
        #  this situation, but it never hurts to be on the safe side."
        # http://effbot.org/zone/sgmlop-handbook.htm
        self.__parser.register(None)
        self.__parser = None
        return self.__builder.close()

    def finish_starttag(self, tag, attrib):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "starttag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if self.verbose:
            msg = "starttag opening '%s'" % tag
            print msg
        self.__builder.start(tag, attrib)
        self.latest_starttag = tag

    def finish_endtag(self, tag):
        # First close any dangling data
        if self.inside_data:
            if self.verbose:
                msg = "endtag closing '%s'" % self.latest_starttag
                print msg
            self.__builder.end(self.latest_starttag)
        self.inside_data = False

        tag = tag.upper()
        if tag != self.latest_starttag:
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
            self.inside_data = True
            self.__builder.data(text)


def main():
    from optparse import OptionParser
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

    ofxparser = OFXParser(verbose=options.verbose,
                        url=options.database)
    ofxparser.parse(FILE)

if __name__ == '__main__':
    main()
