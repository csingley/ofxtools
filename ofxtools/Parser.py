#!/usr/bin/env python
# coding: utf-8
"""
A parser for Open Financial Exchange (OFX) messages,
both version 1 (SGML) and version 2 (XML) formats,
into standard Python `xml.etree.ElementTree.ElementTree` structures,
which interface it implements.

This module only parses the OFX message body, after the OFX header has been
processed and stripped by the `ofxtools.header` module, which is where the
call to `read()` occurs.

Notwithstanding the fact that `ofxtools.TreeBuilder` subclasses the excellent
`xml.etree.ElementTree.Treebuilder` by overriding a fairly minimal set of
methods, the logic is completely different - less efficient and far slower.

If we didn't need to parse OFXv1 (SGML), we'd do better to skip it and
just feed plain XML to `ElementTree`.

The implementation employs re.finditer() and Perl extended regular expressions:
https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups

No ponies were harmed during the production of this parser:
https://stackoverflow.com/questions/1732348/regex-match-open-tags-except-xhtml-self-contained-tags/1732454#1732454
"""


__all__ = ["OFXTree", "TreeBuilder", "ParseError"]


# stdlib imports
import re
import xml.etree.ElementTree as ET
from typing import Tuple, Optional
import logging


# local imports
from ofxtools import config
from ofxtools.header import parse_header, OFXHeaderType
from ofxtools.models.base import Aggregate


logger = logging.getLogger(__name__)


class ParseError(SyntaxError):
    """Exception raised by parsing errors in this module"""


class OFXTree(ET.ElementTree):
    """
    OFX data represented as a hierarchy of `ElementTree.Element` instances.

    This class is an intermediate representation of OFX, focused on
    serialization/deserialization to/from XML/SGML.  By conforming to the
    ElementTree API, pretty much the full range of ElementTree operations are
    made available, including tag modification, branch pruning/grafting,
    XPath search, etc.

    Additionally provides a convert() method to transform this container of
    `ElementTree.Element` instances into a hierarchy of
    `ofxtools.models.base.Aggregate` and `ofxtools.Types.Element` instances,
    which are special-purpose data structures implementing validation, type
    conversion, and general conformance with the OFX specification.

    The inverse operation (i.e. `ofxtools.models` -> `ElementTree.Element`)
    is performed by calling `ofxtools.models.base.Aggregate.to_etree()` on
    the root node of the hierarchy.
    """

    def parse(self, source, parser=None) -> ET.Element:
        """
        Deserialize OFX document into tree of `ElementTree.Element` instances.

        *source* is a file name or file object, *parser* is an optional parser
        instance that defaults to `ofxtools.Parser.TreeBuilder`.

        Overrides ElementTree.ElementTree.parse().
        """
        logger.info(f"Parsing OFX from {source}")
        # Stash the converted OFX header
        self.header, message = self._read(source)
        logger.debug(f"Parsed OFX header: {self.header}")

        # If no parser specified, create default `ofxtools.Parser.TreeBuilder`
        if parser is None:
            parser = TreeBuilder()
        parser.feed(message)

        # ElementTree.TreeBuilder.close() returns the root.
        # Follow ElementTree API and stash as self._root (so all normal
        # ElementTree methods e.g. find() work normally on our subclass).
        self._root = parser.close()
        logger.debug(f"Parsed Element tree root: {self._root}")

        return self._root

    @staticmethod
    def _read(source) -> Tuple[OFXHeaderType, str]:
        """
        Validate/convert OFX header and return it as an instance of
        `ofxtools.header.OFXHeader{V1, V2}`, along with message body as `str`.

        Factored out from `parse()` to facilitate unit testing.
        """
        close_source = False
        if not hasattr(source, "read"):
            source = open(source, "rb")
            close_source = True

        if hasattr(source, "mode") and "b" not in source.mode:
            raise ValueError("Source must be opened in binary mode")

        try:
            header, message = parse_header(source)
        finally:
            if close_source and hasattr(source, "close"):
                source.close()

        return header, message

    def convert(self) -> Aggregate:
        """
        Transform tree of `ElementTree.Element` instances into hierarchy of
        `ofxtools.models.base.Aggregate` & `ofxtools.Types.Element` instances.
        """
        if not isinstance(self._root, ET.Element):
            raise ValueError("Must first call parse() to have data to convert")
        instance = Aggregate.from_etree(self._root)
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
    regex = re.compile(
        r"""<(?P<tag>[A-Z0-9./_ ]+?)>
                (?P<text>[^<]+)?
            (</(?P<closetag>(?P=tag))>)?
            (?P<tail>[^<]+)?
        """,
        re.VERBOSE,
    )

    def feed(self, data: str) -> None:
        """
        Iterate through all tags matched by regex.
        """
        logger.info("Building Element tree from markup body")
        for match in self.regex.finditer(data):
            try:
                groupdict = match.groupdict()

                tail = self._groomstring(groupdict["tail"])
                if tail:
                    raise ParseError(f"Tail text '{tail}' in {match.string}")

                tag = groupdict["tag"]
                text = self._groomstring(groupdict["text"])
                closetag = groupdict["closetag"]
                logger.debug(
                    f"Regex match tag='{tag}', text='{text}', closetag='{closetag}'"
                )
                self._feedmatch(tag, text, closetag)
            except ParseError as err:
                # Report the position of the error
                msg = err.args[0]
                msg += " - position=[{}:{}]".format(match.start(), match.end())
                raise ParseError(msg)

    def _feedmatch(
        self, tag: str, text: Optional[str], closetag: Optional[str]
    ) -> None:
        """
        Route individual regex matches to _start()/_end() according to tag.

        This is factored out into a separate method to facilitate unit testing.
        """
        assert tag
        assert closetag is None or closetag == tag
        if tag.startswith("/"):
            if text:
                raise ParseError(f"Tail text '{text}' after <{tag}>")
            logger.debug(f"Popping tag '{tag[1:]}'")
            self.end(tag[1:])
        else:
            self._start(tag, text, closetag)

    def _start(self, tag: str, text: Optional[str], closetag: Optional[str]) -> None:
        """
        Push a new Element to the stack.

        * If there's text data, it's a leaf.  Write the data and pop it.
        * If there's no text, it's a branch.
            - If regex captured closetag, it's an empty "aggregate"; pop it.
        """
        logger.debug(f"Pushing tag '{tag}'")
        self.start(tag, {})
        if text:
            # OFX "element" i.e. data-bearing leaf
            logger.debug(f"Data text '{text}'")
            self.data(text)
            # End tags are optional for OFXv1 data elements
            # End all elements, whether or not they're explicitly ended
            logger.debug(f"Popping tag '{tag}'")
            self.end(tag)
        elif closetag:
            # Empty OFX "aggregate" branch
            logger.debug(f"Popping tag '{closetag}'")
            self.end(tag)

    @staticmethod
    def _groomstring(string: str) -> Optional[str]:
        """Strips whitespace and returns None for empty string"""
        # Can't strip() None
        string = (string or "").strip()
        if string:
            return string
        return None


def main(*files):
    """
    Simple functional test for impatient developers.
    """
    for file in files:
        ofxparser = OFXTree()
        ofxparser.parse(file)
        response = ofxparser.convert()
        print(response.statements[0].transactions[:])


LOG_LEVELS = {0: logging.WARN, 1: logging.INFO, 2: logging.DEBUG}


if __name__ == "__main__":
    from argparse import ArgumentParser

    argparser = ArgumentParser(description="Parse OFX data; dump transactions")
    argparser.add_argument("file", nargs="+", help="OFX file(s)")
    argparser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Give more output (option can be repeated)",
    )
    args = argparser.parse_args()
    log_level = LOG_LEVELS.get(args.verbose, logging.DEBUG)
    config.configure_logging(log_level)
    main(*args.file)
