# coding: utf-8
"""
Regex-based parser for OFXv1/v2 based on subclasses of ElemenTree from stdlib.
"""
# stdlib imports
import re
import xml.etree.ElementTree as ET


# local imports
from ofxtools.header import OFXHeader
from ofxtools.models import (Aggregate, STMTTRNRS, CCSTMTTRNRS, INVSTMTTRNRS)


class ParseError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class OFXResponse(object):
    """
    Top-level object representing an OFX response converted into Python
    data types, with attributes for convenient access to statements (i.e.
    OFX *STMT aggregates), security descriptions (i.e. OFX SECLIST aggregate),
    and SONRS (server response to signon request).

    After conversion, each of these convenience attributes holds instances
    of various Aggregate subclasses.
    """
    @classmethod
    def from_etree(cls, tree):
        """
        Initialize with ofx.ElementTree instance containing parsed OFX.
        """
        instance = cls()

        # Keep a copy of the parse tree
        instance.tree = tree

        # SONRS - server response to signon request
        sonrs = tree.find('SIGNONMSGSRSV1/SONRS')
        instance.sonrs = Aggregate.from_etree(sonrs)

        # TRNRS - transaction response, which is the main section
        # containing account statements
        instance.statements = []

        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        for stmtClass in (STMTTRNRS, CCSTMTTRNRS, INVSTMTTRNRS):
            tagname = stmtClass.__name__
            for trnrs in tree.findall('*/%s' % tagname):
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                stmtrs = trnrs.find(stmtClass._rsTag)
                if stmtrs is not None:
                    stmt = Aggregate.from_etree(trnrs)
                    instance.statements.append(stmt)

        # SECLIST - list of description of securities referenced by
        # INVSTMT (investment account statement)
        instance.securities = []
        seclist = tree.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is not None:
            instance.securities = Aggregate.from_etree(seclist)

    def __repr__(self):
        s = "<%s fid='%s' org='%s' dtserver='%s' len(statements)=%d len(securities)=%d>"
        return s % (self.__class__.__name__,
                    self.sonrs.fid,
                    self.sonrs.org,
                    str(self.sonrs.dtserver),
                    len(self.statements),
                    len(self.securities),)


class OFXTree(ET.ElementTree):
    """
    Subclass of ElementTree.ElementTree, customized to represent OFX as
    an Element hierarchy.
    """
    def parse(self, source, parser=None):
        """
        Overrides ElementTree.ElementTree.parse() to validate and strip the
        the OFX header before feeding the body tags to custom 
        TreeBuilder subclass (below) for parsing into Element instances.
        """
        source = self._read(source)  # Now it's a string
        source = self._stripHeader(source)  # Now it's OFX payload (SGML/XML)

        # Cut a parser instance
        parser = parser or TreeBuilder
        parser = parser()

        # Then parse tag soup into tree of Elements
        parser.feed(source)

        # ElementTree.TreeBuilder.close() returns the root.
        # Follow ElementTree API and stash as self._root (so all normal
        # ElementTree methods e.g. find() work normally on our subclass).
        self._root = parser.close()

    @staticmethod
    def _read(source):
        """
        Do our best to turn whatever source we're given into a Python string.
        """
        # If our source doesn't follow the file API...
        if not hasattr(source, 'read'):
            # ...try to interpret it as a file
            try:
                source = open(source, 'rb')
            except OSError:
                # ... or else a directly parseable string
                if isinstance(source, str):
                    return source
                else:
                    msg = "Can't read source '{}'".format(source)
                    raise ParseError(msg)
        with source as s:
            source = s.read()
            # BytesIO.read() will return binary not str
            if hasattr(source, 'decode'):
                source = source.decode()
        return source

    @staticmethod
    def _stripHeader(source):
        """ Validate and strip the OFX header """
        return OFXHeader.strip(source)

    def convert(self):
        """ """
        if not isinstance(self._root, ET.Element):
            raise ValueError('Must first call parse() to have data to convert')
        # OFXResponse performs validation & type conversion
        return OFXResponse.from_etree(self)


class TreeBuilder(ET.TreeBuilder):
    """
    OFX parser.

    Overrides ElementTree.TreeBuilder.feed() with a regex-based parser that
    handles both OFXv1(SGML) and OFXv2(XML).
    """
    # The body of an OFX document consists of a series of tags.
    # Each start tag may be followed by text (if a data-bearing element)
    # and optionally an end tag (not mandatory for OFXv1 syntax).
    regex = re.compile(r"""<(?P<tag>[A-Z1-9./ ]+?)>
                            (?P<text>[^<]+)?
                            (</(?P<closetag>(?P=tag))>)?
                            (?P<tail>[^<]+)?
                            """, re.VERBOSE)

    def feed(self, data):
        """
        Iterate through all tags matched by regex.
        """
        for match in self.regex.finditer(data):
            try:
                groupdict = match.groupdict()
                tail = (groupdict['tail'] or '').strip() or None
                if tail:
                    msg = "Tail text '{}' in {}".format(tail, match.string)
                    raise ParseError(msg)
                tag = groupdict['tag']
                text = (groupdict['text'] or '').strip() or None
                closetag = groupdict['closetag']
                self._feedmatch(tag, text, closetag)
            except ParseError as err:
                # Report the position of the error
                msg = err.args[0]
                msg += ' - position=[{}:{}]'.format(match.start(), match.end())
                raise ParseError(msg)

    def _feedmatch(self, tag, text, closetag):
        """
        Route individual regex matches to _start()/_end() according to tag.

        This is factored out into a separate method to facilitate unit testing.
        """
        assert closetag is None or closetag == tag
        if tag.startswith('/'):
            self._end(tag[1:], text)
        else:
            self._start(tag, text, closetag)

    def _start(self, tag, text, closetag):
        """
        Push a new Element to the stack.

        * If there's text data, it's a leaf.  Write the data and pop it.
        * If there's no text, it's a branch.
            - If regex captured closetag, it's an empty "aggregate"; pop it.
        """
        assert tag
        self.start(tag, {})
        if text:
            # OFX "element" (i.e. data-bearing leaf)
            self.data(text)
            # End tags are optional for OFXv1 data elements
            # End all elements, whether or not they're explicitly ended
            assert closetag is None or closetag == tag
            self.end(tag)
        elif closetag:
            # Empty OFX "aggregate" branch
            assert closetag == tag
            self.end(tag)

    def _end(self, tag, text):
        """
        Pop the top Element from the stack.
        """
        if text:
            msg = "Tail text '{}' after </{}>".format(text, tag)
            raise ParseError(msg.format(tag, text))
        self.end(tag)


def main():
    from argparse import ArgumentParser

    argparser = ArgumentParser(description='Parse OFX data')
    argparser.add_argument('file', nargs='+', help='OFX file(s)')
    args = argparser.parse_args()

    for file in args.file:
        ofxparser = OFXTree()
        ofxparser.parse(file)
        response = ofxparser.convert()


if __name__ == '__main__':
    main()
