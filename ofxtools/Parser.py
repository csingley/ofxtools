# coding: utf-8
"""
Regex-based parser for OFXv1/v2 based on subclasses of ElemenTree from stdlib.
"""

# stdlib imports
import re
import xml.etree.ElementTree as ET
# ElementTree's new C accelerators will break our parser; use old Python version
if '_Element_Py' in dir(ET):
    ET.Element = ET._Element_Py

    def SubElement(parent, tag, attrib={}, **extra):
        """Subelement factory which creates an element instance, and appends it
        to an existing parent.

        The element tag, attribute names, and attribute values can be either
        bytes or Unicode strings.

        *parent* is the parent element, *tag* is the subelements name, *attrib* is
        an optional directory containing element attributes, *extra* are
        additional attributes given as keyword arguments.

        We recreate the old pure Python xml.etree.ElementTree.SubElement() in order
        to make it actually return an instance of our custom Element subclass.

        """
        attrib = attrib.copy()
        attrib.update(extra)
        element = parent.makeelement(tag, attrib)
        parent.append(element)
        return element

    ET.SubElement = SubElement


# local imports
from ofxtools.header import OFXHeader
from ofxtools.Response import OFXResponse


class ParseError(SyntaxError):
    """ Exception raised by parsing errors in this module """
    pass


class Element(ET.Element):
    """ Parse tree node """
    def _flatten(self):
        """
        Recurse through aggregate and flatten; return an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
        """
        aggs = {}
        leaves = {}
        for child in self:
            tag = child.tag
            data = child.text or ''
            data = data.strip()
            if data:
                # it's a data-bearing leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # it's an aggregate.
                assert tag not in aggs
                aggs.update(child._flatten())
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggs.keys():
            assert key not in leaves
        leaves.update(aggs)

        return leaves


class OFXTree(ET.ElementTree):
    """
    OFX parse tree.

    Overrides ElementTree.ElementTree.parse() to validate and strip the
    the OFX header before feeding the body tags to TreeBuilder
    """
    element_factory = Element

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
        parser = TreeBuilder(element_factory=self.element_factory)
        parser.feed(source)
        self._root = parser.close()

    def convert(self):
        if not hasattr(self, '_root'):
            raise ValueError('Must first call parse() to have data to convert')
        # OFXResponse performs validation & type conversion
        return OFXResponse(self)


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
            text = (text or '').strip() # None has no strip() method
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
                    err.message += ' </%s>' % tag # FIXME
                    raise ParseError(err.message)
            else:
                # OFX "aggregate" (tagged branch w/ no data)
                if tag.startswith('/'):
                    # aggregate end tag
                    try:
                        self.end(tag[1:])
                    except ParseError as err:
                        err.message += ' </%s>' % tag # FIXME
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
                           err.message += ' </%s>' % tag # FIXME
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
