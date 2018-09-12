# coding: utf-8
"""
Regex-based parser for OFXv1/v2 subclassing ElemenTree from stdlib.
"""
# stdlib imports
import re
import xml.etree.ElementTree as ET


# local imports
from ofxtools.header import OFXHeader
from ofxtools.models.base import Aggregate


class ParseError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


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
        header, ofx = self._read(source)

        # Cut a parser instance
        parser = parser or TreeBuilder
        parser = parser()

        # Then parse tag soup into tree of Elements
        parser.feed(ofx)

        # ElementTree.TreeBuilder.close() returns the root.
        # Follow ElementTree API and stash as self._root (so all normal
        # ElementTree methods e.g. find() work normally on our subclass).
        self._root = parser.close()

    def _read(self, source):
        """
        """
        # If our source doesn't follow the file API, try to interpret it
        # as a file path
        if not hasattr(source, 'read'):
            try:
                source = open(source, 'rb')
            except OSError:
                msg = "Can't read source '{}'".format(source)
                raise ParseError(msg)

        header, ofx = OFXHeader.parse(source)
        return header, ofx

    def convert(self):
        """ """
        if not isinstance(self._root, ET.Element):
            raise ValueError('Must first call parse() to have data to convert')
        # OFXResponse performs validation & type conversion
        # return OFXResponse.from_etree(self)
        instance = Aggregate.from_etree(self._root)

        # Keep a copy of the parse tree
        instance.tree = self

        return instance


class TreeBuilder(ET.TreeBuilder):
    """
    OFX parser.

    Overrides ElementTree.TreeBuilder.feed() with a regex-based parser that
    handles both OFXv1(SGML) and OFXv2(XML).
    """
    # The body of an OFX document consists of a series of tags.
    # Each start tag may be followed by text (if a data-bearing element)
    # and optionally an end tag (not mandatory for OFXv1 syntax).
    regex = re.compile(r"""<(?P<tag>[A-Z0-9./ ]+?)>
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

                tail = self._groomstring(groupdict['tail'])
                if tail:
                    msg = "Tail text '{}' in {}".format(tail, match.string)
                    raise ParseError(msg)

                tag = groupdict['tag']
                text = self._groomstring(groupdict['text'])
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
        assert tag
        assert closetag is None or closetag == tag
        if tag.startswith('/'):
            if text:
                msg = "Tail text '{}' after <{}>".format(text, tag)
                raise ParseError(msg.format(tag, text))
            self.end(tag[1:])
        else:
            self._start(tag, text, closetag)

    def _start(self, tag, text, closetag):
        """
        Push a new Element to the stack.

        * If there's text data, it's a leaf.  Write the data and pop it.
        * If there's no text, it's a branch.
            - If regex captured closetag, it's an empty "aggregate"; pop it.
        """
        self.start(tag, {})
        if text:
            # OFX "element" (i.e. data-bearing leaf)
            self.data(text)
            # End tags are optional for OFXv1 data elements
            # End all elements, whether or not they're explicitly ended
            self.end(tag)
        elif closetag:
            # Empty OFX "aggregate" branch
            self.end(tag)

    @staticmethod
    def _groomstring(string):
        """ Strips whitespace and returns None for empty string """
        # Can't strip() None
        string = (string or '').strip()
        return string or None


def main():
    from argparse import ArgumentParser

    argparser = ArgumentParser(description='Parse OFX data')
    argparser.add_argument('file', nargs='+', help='OFX file(s)')
    args = argparser.parse_args()

    for file in args.file:
        ofxparser = OFXTree()
        ofxparser.parse(file)
        response = ofxparser.convert()
        print(response.statements[0].transactions[:])


if __name__ == '__main__':
    main()
