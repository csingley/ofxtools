# coding: utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# stdlib imports
import xml.etree.ElementTree as ET


# local imports
import ofxtools.models
from ofxtools.Types import (
    Element,
    DateTime,
)


class classproperty(property):
    """ Decorator that turns a classmethod into a property """
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class Aggregate(object):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML parent
    node that contains no data.

    Performs validation & type conversion for class attributes of type
    Element, SubAggregate, Unsupported.

    The constructor takes an instance of ofx.Parser.Element.
    """
    mutexes = []

    def __init__(self, elem):
        """ """
        attributes = {el.tag.lower(): (el.text or el) for el in elem}
        # Set instance attributes for all SubAggregates and Elements in the
        # spec (i.e. defined on the class), using values from input attributes
        # if available, or None if not in attributes.
        for attr in self.spec:
            value = attributes.pop(attr, None)
            try:
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        # Check that no attributes (not part of the spec) are left over
        if attributes:
            msg = "Aggregate {} does not define {}".format(
                self.__class__.__name__, str(list(attributes.keys()))
            )
            raise ValueError(msg)

    @staticmethod
    def from_etree(elem):
        """
        Look up the Aggregate subclass for a given ofx.Parser.Element and
        feed it the Element to instantiate an Aggregate corresponding to the
        Element.tag.

        Main entry point for type conversion from ElementTree to Aggregate.
        """
        try:
            SubClass = getattr(ofxtools.models, elem.tag)
        except AttributeError:
            msg = "ofxtools.models doesn't define {}".format(elem.tag)
            raise ValueError(msg)
        SubClass.verify(elem)
        SubClass.groom(elem)
        instance = SubClass(elem)
        return instance

    @classmethod
    def verify(cls, elem):
        """
        Enforce Aggregate-level structural constraints of the OFX spec.

        Throw an error for Elements containing sub-Elements that are
        mutually exclusive per the OFX spec,

        Extend in subclass.
        """
        for mutex in cls.mutexes:
            if (elem.find(mutex[0]) is not None and
                    elem.find(mutex[1]) is not None):
                msg = "{} may not contain both {} and {}".format(
                    elem.tag, mutex[0], mutex[1])
                raise ValueError(msg)

    @staticmethod
    def groom(elem):
        """
        Modify incoming XML data to play nice with our Python scheme.

        Extend in subclass.
        """
        pass

    def __repr__(self):
        attrs = ['%s=%r' % (attr, str(getattr(self, attr)))
                 for attr in self.elements
                 if getattr(self, attr) is not None]
        return '<%s %s>' % (self.__class__.__name__, ' '.join(attrs))

    def to_etree(self):
        """ """
        root = ET.Element(self.__class__.__name__)
        for spec in self.spec:
            value = getattr(self, spec)
            if value is None:
                continue
            elif isinstance(value, Aggregate):
                child = value.to_etree()
                root.append(child)
            else:
                converter = self.__class__.__dict__[spec]
                text = converter.unconvert(value)
                ET.SubElement(root, spec.upper()).text = text
        return root

    @classproperty
    @classmethod
    def elements(cls):
        """
        dict of all Aggregate attributes that are Elements not SubAggregates
        """
        dct = {}
        for parent in reversed(cls.__mro__):
            dct.update({k: v for k, v in parent.__dict__.items()
                        if isinstance(v, Element)
                        and not isinstance(v, SubAggregate)})
        return dct

    @classproperty
    @classmethod
    def subaggregates(cls):
        """ dict of all Aggregate attributes that are SubAggregates """
        dct = {}
        for parent in reversed(cls.__mro__):
            dct.update({k: v for k, v in parent.__dict__.items()
                        if isinstance(v, SubAggregate)})
        return dct

    @classproperty
    @classmethod
    def unsupported(cls):
        """ dict of all Aggregate attributes that are Unsupported """
        dct = {}
        for parent in reversed(cls.__mro__):
            dct.update({k: v for k, v in parent.__dict__.items()
                        if isinstance(v, Unsupported)})
        return dct

    @classproperty
    @classmethod
    def spec(cls):
        """
        dict of all Aggregate attributes that are
        Elements/SubAggregates/Unsupported
        """
        dct = {}
        for parent in reversed(cls.__mro__):
            dct.update({k: v for k, v in parent.__dict__.items()
                        if isinstance(v,
                                      (SubAggregate, Element, Unsupported))})
        return dct


class List(Aggregate, list):
    """
    Base class for OFX *LIST
    """
    memberTags = []

    def __init__(self, elem):
        list.__init__(self)
        for member in elem:
            if member.tag not in self.memberTags:
                msg = "{} can't contain {}".format(self.__class__.__name__,
                                                   member.tag)
                raise ValueError(msg)
            self.append(Aggregate.from_etree(member))

    def to_etree(self):
        """ """
        root = ET.Element(self.__class__.__name__)
        for spec in self.spec:
            value = getattr(self, spec)
            if value is None:
                continue
            else:
                converter = self.__class__.__dict__[spec]
                text = converter.unconvert(value)
                ET.SubElement(root, spec.upper()).text = text
        # Append list items
        for member in self:
            print("MEMBER=%s" % member)
            root.append(member.to_etree())
        return root

    def __hash__(self):
        """
        HACK - as a subclass of list, List is unhashable, but we need to
        use it as a dict key in Type.Element.{__get__, __set__}
        """
        return object.__hash__(self)

    def __repr__(self):
        return '<{} len={}'.format(self.__class__.__name__, len(self))


class TranList(List):
    """
    Base class for OFX *TRANLIST
    """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    def __init__(self, elem):
        # The first two children of *TRANLIST are DTSTART/DTEND.
        dtstart, dtend = elem[:2]
        if dtstart.tag != 'DTSTART':
            msg = "{} 1st member must be DTSTART, not {}".format(
                self.__class__.__name__, dtstart.tag)
            raise ValueError(msg)
        elem.remove(dtstart)
        self.dtstart = dtstart.text
        if dtend.tag != 'DTEND':
            msg = "{} 2nd member must be DTEND, not {}".format(
                self.__class__.__name__, dtend.tag)
            raise ValueError(msg)
        elem.remove(dtend)
        self.dtend = dtend.text
        super(TranList, self).__init__(elem)

    def __repr__(self):
        return '<{} dtstart={} dtend={} len={}'.format(
            self.__class__.__name__, self.dtstart, self.dtend, len(self))


class SubAggregate(Element):
    """
    Aggregate that is a child of this parent Aggregate
    """
    def _init(self, *args, **kwargs):
        args = list(args)
        agg = args.pop(0)
        assert issubclass(agg, Aggregate)
        self.type = agg
        super(SubAggregate, self)._init(*args, **kwargs)

    def convert(self, value):
        """ """
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        if isinstance(value, self.type):
            return value
        return Aggregate.from_etree(value)


class Unsupported(object):
    """ 
    Null Aggregate/Element - not implemented (yet)
    """
    def __get__(self, instance, type_):
        pass

    def __set__(self, instance, value):
        pass
