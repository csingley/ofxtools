# coding: utf-8
""" Common classes reused by unit tests in this package """

# stdlib imports
from xml.etree.ElementTree import SubElement
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate


class TestAggregate(object):
    """ """
    __test__ = False
    requiredElements = ()
    optionalElements = ()

    @property
    def root(self):
        """Define in subclass"""
        raise NotImplementedError

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                root = deepcopy(self.root)
                child = root.find(tag)
                try:
                    root.remove(child)
                except TypeError:
                    msg = "Can't find {} (from requiredElements) under {}"
                    raise ValueError(msg.format(tag, root.tag))
                with self.assertRaises(ValueError):
                    Aggregate.from_etree(root)

    def testOptional(self):
        if self.optionalElements:
            for tag in self.optionalElements:
                root = deepcopy(self.root)
                child = root.find(tag)
                try:
                    root.remove(child)
                except TypeError:
                    msg = "Can't find {} (from optionalElements) under {}"
                    raise ValueError(msg.format(tag, root.tag))
                Aggregate.from_etree(root)

    def testExtraElement(self):
        root = deepcopy(self.root)
        SubElement(root, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def oneOfTest(self, tag, texts):
        # Make sure OneOf validator allows all legal values and disallows
        # illegal values
        for text in texts:
            root = deepcopy(self.root)
            target = root.find('.//%s' % tag)
            target.text = text
            Aggregate.from_etree(root)

        root = deepcopy(self.root)
        target = root.find('.//%s' % tag)
        target.text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)
