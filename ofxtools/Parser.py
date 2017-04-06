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


class OFXTree(ET.ElementTree):
    """
    OFX parse tree.

    Overrides ElementTree.ElementTree.parse() to validate and strip the
    the OFX header before feeding the body tags to TreeBuilder
    """
    def parse(self, source):
        if not hasattr(source, 'read'):
            source = open(source)
        with source as s:
            source = s.read()
            if hasattr(source, 'decode'):
                source = source.decode()

        # Validate and strip the OFX header
        source = OFXHeader.strip(source)

        # Then parse tag soup into tree of Elements
        # parser = TreeBuilder(element_factory=self.element_factory)
        parser = TreeBuilder()
        parser.feed(source)
        self._root = parser.close()

    def convert(self):
        if not hasattr(self, '_root'):
            raise ValueError('Must first call parse() to have data to convert')
        # OFXResponse performs validation & type conversion
        return OFXResponse(self)


class OFXResponse(object):
    """
    Top-level object representing an OFX response converted into Python
    data types, with attributes for convenient access to statements (i.e.
    OFX *STMT aggregates), security descriptions (i.e. OFX SECLIST aggregate),
    and SONRS (server response to signon request).

    After conversion, each of these convenience attributes holds instances
    of various Aggregate subclasses.
    """
    def __init__(self, tree):
        """
        Initialize with ofx.ElementTree instance containing parsed OFX.
        """
        # Keep a copy of the parse tree
        self.tree = tree

        # SONRS - server response to signon request
        sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
        self.sonrs = Aggregate.from_etree(sonrs)

        # TRNRS - transaction response, which is the main section
        # containing account statements
        self.statements = []

        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        for stmtClass in (STMTTRNRS, CCSTMTTRNRS, INVSTMTTRNRS):
            tagname = stmtClass.__name__
            for trnrs in self.tree.findall('*/%s' % tagname):
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                stmtrs = trnrs.find(stmtClass._rsTag)
                if stmtrs is not None:
                    stmt = Aggregate.from_etree(trnrs)
                    self.statements.append(stmt)

        # SECLIST - list of description of securities referenced by
        # INVSTMT (investment account statement)
        self.securities = []
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is not None:
            self.securities = Aggregate.from_etree(seclist)

    def __repr__(self):
        s = "<%s fid='%s' org='%s' dtserver='%s' len(statements)=%d len(securities)=%d>"
        return s % (self.__class__.__name__,
                    self.sonrs.fid,
                    self.sonrs.org,
                    str(self.sonrs.dtserver),
                    len(self.statements),
                    len(self.securities),
                   )


class TreeBuilder(ET.TreeBuilder):
    """
    OFX parser.

    Overrides ElementTree.TreeBuilder.feed() with a regex-based parser that
    handles both OFXv1(SGML) and OFXv2(XML).
    """
    # The body of an OFX document consists of a series of tags.
    # Each start tag may be followed by text (if a data-bearing element)
    # and optionally an end tag (not mandatory for OFXv1 syntax).
    regex = re.compile(r"""<(?P<TAG>[A-Z1-9./]+?)>
                            (?P<TEXT>[^<]+)?
                            (</(?P=TAG)>)?
                            """, re.VERBOSE)

    def feed(self, data):
        """
        Iterate through all tags matched by regex.
        For data-bearing leaf "elements", use TreeBuilder's methods to
            push a new Element, process the text data, and end the element.
        For non-data-bearing "aggregate" branches, parse the tag to distinguish
            start/end tag, and push or pop the Element accordingly.
        """
        for match in self.regex.finditer(data):
            tag, text, closeTag = match.groups()
            text = (text or '').strip()  # None has no strip() method
            if len(text):
                # OFX "element" (i.e. data-bearing leaf)
                if tag.startswith('/'):
                    msg = "<%s> is a closing tag, but has trailing text: '%s'"\
                            % (tag, text)
                    raise ParseError(msg)
                self.start(tag, {})
                self.data(text)
                # End tags are optional for OFXv1 data elements
                # End them all, whether or not they're explicitly ended
                try:
                    self.end(tag)
                except ParseError as err:
                    err.message += ' </%s>' % tag  # FIXME
                    raise ParseError(err.message)
            else:
                # OFX "aggregate" (tagged branch w/ no data)
                if tag.startswith('/'):
                    # aggregate end tag
                    try:
                        self.end(tag[1:])
                    except ParseError as err:
                        err.message += ' </%s>' % tag  # FIXME
                        raise ParseError(err.message)
                else:
                    # aggregate start tag
                    self.start(tag, {})
                    # empty aggregates are legal, so handle them
                    if closeTag:
                        # regex captures the entire closing tag
                        assert closeTag.replace(tag, '') == '</>'
                        try:
                            self.end(tag)
                        except ParseError as err:
                            err.message += ' </%s>' % tag  # FIXME
                            raise ParseError(err.message)

    def end(self, tag):
        try:
            super(TreeBuilder, self).end(tag)
        except AssertionError as err:
            # HACK: ET.TreeBuilder.end() raises an AssertionError for internal
            # errors generated by ET.TreeBuilder._flush(), but also for ending
            # tag mismatches, which are problems with the data rather than the
            # parser.  We want to pass on the former but handle the latter;
            # however, the only difference is the error message.
            if 'end tag mismatch' in err.message:
                raise ParseError(err.message)
            else:
                raise


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
