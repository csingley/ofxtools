# coding: utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# stdlib imports
import xml.etree.ElementTree as ET
from collections import OrderedDict


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

    def __init__(self, **kwargs):
        """ """
        # Set instance attributes for all SubAggregates and Elements in the
        # spec (i.e. defined on the class), using values from input attributes
        # if available, or None if not in attributes.
        for attr in self.spec:
            value = kwargs.pop(attr, None)
            try:
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        # Check that no attributes (not part of the spec) are left over
        if kwargs:
            msg = "Aggregate {} does not define {}".format(
                self.__class__.__name__, str(list(kwargs.keys()))
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
        args = []
        kwargs = {}
        if issubclass(SubClass, List):
            if issubclass(SubClass, TranList):
                dtstart, dtend = elem[:2]
                args = [dtstart.text, dtend.text]
                elem.remove(dtstart)
                elem.remove(dtend)
            args.extend([Aggregate.from_etree(el) for el in elem])
        else:
            kwargs = {el.tag.lower(): (el.text or el) for el in elem}
        instance = SubClass(*args, **kwargs)
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
        Return True to mark this element to be skipped.

        Extend in subclass.
        """
        pass

    @staticmethod
    def ungroom(elem):
        """
        Reverse groom() when converting back to ElementTree.

        Extend in subclass.
        """
        pass

    def _repr(self):
        """ """
        attrs = [(attr, repr(getattr(self, attr)))
                 for attr in self.spec
                 if getattr(self, attr) is not None]
        return attrs

    def __repr__(self):
        attrs = ['{}={}'.format(*attr) for attr in self._repr()]
        return '<{}({})>'.format(self.__class__.__name__, ', '.join(attrs))

    def to_etree(self):
        """ """
        root = ET.Element(self.__class__.__name__)
        for spec in self.spec:
            value = getattr(self, spec)
            if value is None:
                continue
            elif isinstance(value, Aggregate):
                child = value.to_etree()
                value.ungroom(child)
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
        dct = OrderedDict()
        for k, v in cls.__dict__.items():
            if isinstance(v, Element) and not isinstance(v, SubAggregate):
                dct[k] = v
        return dct

    @classproperty
    @classmethod
    def subaggregates(cls):
        """ dict of all Aggregate attributes that are SubAggregates """
        dct = OrderedDict()
        for k, v in cls.__dict__.items():
            if isinstance(v, SubAggregate):
                dct[k] = v
        return dct

    @classproperty
    @classmethod
    def unsupported(cls):
        """ dict of all Aggregate attributes that are Unsupported """
        dct = OrderedDict()
        for k, v in cls.__dict__.items():
            if isinstance(v, Unsupported):
                dct[k] = v
        return dct

    @classproperty
    @classmethod
    def spec(cls):
        """
        dict of all Aggregate attributes that are
        Elements/SubAggregates/Unsupported
        """
        dct = OrderedDict()
        for k, v in cls.__dict__.items():
            if isinstance(v, (SubAggregate, Element, Unsupported)):
                dct[k] = v
        return dct

    def __getattr__(self, attr):
        """ Proxy access to attributes of SubAggregates """
        for subaggregate in self.subaggregates:
            subagg = getattr(self, subaggregate)
            try:
                return getattr(subagg, attr)
            except AttributeError:
                continue
        raise AttributeError("'{}' object has no attribute '{}'".format(
            self.__class__.__name__, attr))


class List(Aggregate, list):
    """
    Base class for OFX *LIST
    """
    memberTags = []

    def __init__(self, *members):
        list.__init__(self)
        for member in members:
            if member.__class__.__name__ not in self.memberTags:
                msg = "{} can't contain {}".format(self.__class__.__name__,
                                                   member.__class__.__name__)
                raise ValueError(msg)
            self.append(member)

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
            root.append(member.to_etree())
        return root

    def __hash__(self):
        """
        HACK - as a subclass of list, List is unhashable, but we need to
        use it as a dict key in Type.Element.{__get__, __set__}
        """
        return object.__hash__(self)

    def __repr__(self):
        return '<{} len={}>'.format(self.__class__.__name__, len(self))


class TranList(List):
    """
    Base class for OFX *TRANLIST
    """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    def __init__(self, dtstart, dtend, *members):
        self.dtstart = dtstart
        self.dtend = dtend
        super(TranList, self).__init__(*members)

    def __repr__(self):
        return "<{} dtstart='{}' dtend='{}' len={}>".format(
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
 
    def __repr__(self):
        repr = "<SubAggregate {}>".format(self.type)
        return repr


class Unsupported(object):
    """
    Null Aggregate/Element - not implemented (yet)
    """
    def __get__(self, instance, type_):
        pass

    def __set__(self, instance, value):
        pass

    def __repr__(self):
        return "<Unsupported>"
