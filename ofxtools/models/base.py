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
    Element, DateTime, String, Bool, InstanceCounterMixin)


class classproperty(property):
    """ Decorator that turns a classmethod into a property """
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class Aggregate:
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML parent
    node that contains no data.

    Performs validation & type conversion for class attributes of type
    ``Element``, ``SubAggregate``, ``Unsupported``.

    The alternate ``from_etree()`` instance constructor takes an instance of
    ``xml.etree.ElementTree.Element``.
    """
    # Validation constraints used by ``validate_kwargs()``.
    # Sequences of tuples (type str) defining mutually exclusive child tags.
    # Aggregate MAY have a child from  `optionalMutexes``;
    # MUST contain child from ``requiredMutexes``.
    optionalMutexes = []
    requiredMutexes = []

    def __init__(self, **kwargs):
        self.validate_kwargs(kwargs)

        # Set instance attributes for all SubAggregates and Elements defined in
        # ``Aggregate.spec`` (i.e. class attributes), defaulting to None if not
        # given by kwargs
        for attr in self.spec:
            value = kwargs.pop(attr, None)
            try:
                # Each member of ``Aggregate.spec`` is a string referring
                # to a class attribute that's a subclass of ``Types.Element``.
                # These are data descriptors that call the subclass's
                # ``convert()`` in its overriden  ``__set__()``.
                # This is where the type conversion happens.
                #
                # If ``attr`` (i.e. key from kwargs) refers to a SubAggregate
                # instance, then that SubAggregate instance gets overwritten on
                # this Aggregate instance by the corresponding kwargs value,
                # after its been type-converted.
                # (This is pretty normal behavior for an __init__() function)
                #
                # If ``attr`` (i.e. key from kwargs) refers to an instance
                # of a ``Types.Element`` subclass (i.e. a data-bearing leaf
                # node as defined in the OFX spec), then setting its value
                # invokes the proxy caching logic in ``ofxtools.Types`` (q.v.)
                # (This is the weird part)
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        # Check that all args have been consumed, i.e. we haven't been passed
        # any args that aren't in ``self.spec()``.
        if kwargs:
            msg = "Aggregate {} does not define {}".format(
                self.__class__.__name__, str(list(kwargs.keys()))
            )
            raise ValueError(msg)

    @classmethod
    def validate_kwargs(cls, kwargs):
        """
        Extra validation constraints from the OFX spec not captured by
        ofxtools class definition or type validators.
        """
        # Aggregate MAY contain at most one child from each tuple
        for (attr0, attr1) in cls.optionalMutexes:
            val0 = kwargs.get(attr0, None)
            val1 = kwargs.get(attr1, None)
            if val0 and val1:
                msg = "{} may not set both {} and {}"
                raise ValueError(msg.format(cls.__name__, attr0, attr1))

        # Aggregate MUST contain exactly one child from each tuple
        for choices in cls.requiredMutexes:
            count = sum([kwargs.get(ch, None) is not None for ch in choices])
            if count != 1:
                args = ', '.join(['{}={}'.format(ch, kwargs.get(ch, None))
                                  for ch in choices])
                msg = "{}({}): must contain exactly 1 of [{}]"
                raise ValueError(msg.format(cls.__name__, args, choices))

    @classmethod
    def from_etree(cls, elem):
        """
        Instantiate from ``xml.etree.ElementTree.Element`` instead of kwargs.

        Look up `Aggregate`` subclass corresponding to ``Element.tag``;
        parse the Element structure into (args, kwargs) and pass those
        to the subclass __init__().

        Main entry point for type conversion from ``ET.Element`` to
        ``Aggregate``.
        """
        if not isinstance(elem, ET.Element):
            msg = "Bad type {} - should be xml.etree.ElementTree.Element"
            raise ValueError(msg.format(type(elem)))
        try:
            SubClass = getattr(ofxtools.models, elem.tag)
        except AttributeError:
            msg = "ofxtools.models doesn't define {}".format(elem.tag)
            raise ValueError(msg)

        # Hook to modify incoming ``ET.Element`` before conversion
        SubClass.groom(elem)

        args, kwargs = SubClass._etree2args(elem)
        instance = SubClass(*args, **kwargs)
        return instance

    @staticmethod
    def groom(elem):
        """
        Modify incoming ``ET.Element`` to play nice with our Python schema.

        Extend in subclass.
        """
        pass

    @classmethod
    def _etree2args(cls, elem):
        """
        Extract args to pass to __init__() from ``ET.Element``.

        Generic ``Aggregate`` subclass __init__() accepts only keyword args.
        """
        # Verify that SubElements appear in the correct order
        spec = list(cls.spec)
        children = [(el.tag.lower(), el.text or el) for el in elem]

        def indexOrRaise(tag, value):
            try:
                return spec.index(tag)
            except ValueError:
                msg = "Aggregate {} does not define {}".format(
                    cls.__name__, tag)
                raise ValueError(msg)

        indices = [indexOrRaise(*child) for child in children]
        if indices != sorted(indices):
            msg = "{} SubElements out of order: {}"
            raise ValueError(msg.format(cls.__name__,
                                        [c[0] for c in children]))

        args = []

        # ``dict.__init__()`` updates duplicate keys, so we can't use that.
        # In OFX, only *LIST may contain repeated child tags.
        kwargs = {}
        for tag, value in children:
            if tag in kwargs:
                msg = "{} contains multiple {}"
                raise ValueError(msg.format(cls.__name__, tag))
            kwargs[tag] = value

        return args, kwargs

    def to_etree(self):
        """
        Convert self and children to `ElementTree.Element` hierarchy
        """
        cls = self.__class__
        root = ET.Element(cls.__name__)
        for spec in self.spec:
            value = getattr(self, spec)
            if value is None:
                continue
            elif isinstance(value, Aggregate):
                child = value.to_etree()
                # Hook to modify `ET.ElementTree` after conversion
                value.ungroom(child)
                root.append(child)
            else:
                converter = cls.__dict__[spec]
                text = converter.unconvert(value)
                ET.SubElement(root, spec.upper()).text = text
        return root

    @staticmethod
    def ungroom(elem):
        """
        Reverse groom() when converting back to ElementTree.

        Extend in subclass.
        """
        pass

    @classmethod
    def _ordered_attrs(cls, predicate):
        """
        Filter cls.__dict__ for items matching the given predicate and return
        them as an OrderedDict in the same order they're declared in the class
        definition.

        N.B. predicate tests *values* of cls.__dict__
             (not keys i.e. attribute names)
        """
        match_items = [(k, v) for k, v in cls.__dict__.items() if predicate(v)]
        match_items.sort(key=lambda it: it[1]._counter)
        return OrderedDict(match_items)

    @classproperty
    @classmethod
    def spec(cls):
        """
        OrderedDict of all Aggregate attributes that are
        Elements/SubAggregates/Unsupported.

        N.B. SubAggregate is a subclass of Element.
        """
        return cls._ordered_attrs(lambda v:
                                  isinstance(v, (Element, Unsupported)))

    @classproperty
    @classmethod
    def elements(cls):
        """
        OrderedDict of all Aggregate attributes that are Elements but not
        SubAggregates.
        """
        return cls._ordered_attrs(lambda v:
                                  isinstance(v, Element)
                                  and not isinstance(v, SubAggregate))

    @classproperty
    @classmethod
    def subaggregates(cls):
        """
        OrderedDict of all Aggregate attributes that are SubAggregates.
        """
        return cls._ordered_attrs(lambda v:
                                  isinstance(v, SubAggregate))

    @classproperty
    @classmethod
    def unsupported(cls):
        """
        OrderedDict of all Aggregate attributes that are Unsupported.
        """
        return cls._ordered_attrs(lambda v:
                                  isinstance(v, Unsupported))

    @property
    def _spec_repr(self):
        """
        Sequence of (name, repr()) for each item in the subclass spec
        (see property above) that has a value for this instance.

        Used by __repr__().
        """
        attrs = [(attr, repr(getattr(self, attr)))
                 for attr in self.spec
                 if getattr(self, attr) is not None]
        return attrs

    def __repr__(self):
        attrs = ['{}={}'.format(*attr) for attr in self._spec_repr]
        return '<{}({})>'.format(self.__class__.__name__, ', '.join(attrs))

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


class SubAggregate(Element):
    """
    Aggregate that is a child of this parent Aggregate.

    SubAggregate instances appear only in the model class definitions
    (Aggregate subclasses).  Their main utility is to define the ``spec``
    class attribute for a model class, via ``Aggregate._ordered_attrs()``.

    Actual model instances replace these SubAggregate instances with Aggregate
    instances; cf. ``Aggregate.__init__()`` call to ``setattr()``.
    """
    def _init(self, *args, **kwargs):
        args = list(args)
        agg = args.pop(0)
        assert issubclass(agg, Aggregate)
        self.type = agg
        super()._init(*args, **kwargs)

    def convert(self, value):
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        if isinstance(value, self.type):
            return value
        return Aggregate.from_etree(value)

    # This doesn't get used
    #  def __repr__(self):
        #  repr = "<SubAggregate {}>".format(self.type)
        #  return repr


class Unsupported(InstanceCounterMixin):
    """
    Null Aggregate/Element - not implemented (yet)
    """
    def __get__(self, instance, type_):
        pass

    def __set__(self, instance, value):
        pass

    def __repr__(self):
        return "<Unsupported>"


class List(Aggregate, list):
    """
    Base class for OFX *LIST
    """
    # ``List.metadataTags`` means fixed child ``Elements``  (in the OFX spec)
    # preceding the variable-length sequence of contained ``Aggregates``.
    # Define as sequence of OFX tags (type str) corresponding to __init__()
    # positional args - order is significant.
    # Used by ``_etree2args()`` to parse args.
    metadataTags = []
    # Sequence of OFX tags (type str) allowed to occur as contained
    # ``Aggregates``.
    # Used by ``__init__()`` to validate args.
    dataTags = []

    def __init__(self, *members):
        list.__init__(self)

        for member in members:
            cls_name = member.__class__.__name__
            if cls_name not in self.dataTags:
                msg = "{} can't contain {} as List data"
                raise ValueError(msg.format(self.__class__.__name__, cls_name))
            self.append(member)

    @classmethod
    def _etree2args(cls, elem):
        """
        Extract args to pass to __init__() from ``ET.Element``.

        ``List.__init__()`` accepts only positional args
        (unlike ``Aggregate.__init__()``)
        """
        # Remove List metadata and pass as positional args before list members
        def find(tag):
            child = elem.find(tag)
            if child is not None:
                elem.remove(child)
                child = child.text
            return child

        args = [find(tag) for tag in cls.metadataTags]

        # Add list members as variable-length positional args
        args.extend([Aggregate.from_etree(el) for el in elem])

        kwargs = {}
        return args, kwargs

    def to_etree(self):
        """
        Convert self and children to `ElementTree.Element` hierarchy
        """
        cls = self.__class__
        root = ET.Element(cls.__name__)
        # Append items enumerated in the class definition
        # (i.e. direct child Elements of the *LIST defined in the OFX spec)
        # - this is used by subclasses (e.g. Tranlist), not directly by List
        for spec in self.spec:
            value = getattr(self, spec)
            if value is not None:
                converter = cls.__dict__[spec]
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
    """ Base class for OFX *TRANLIST """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    metadataTags = ['DTSTART', 'DTEND']

    def __init__(self, dtstart, dtend, *members):
        self.dtstart = dtstart
        self.dtend = dtend
        super().__init__(*members)

    def __repr__(self):
        return "<{} dtstart='{}' dtend='{}' len={}>".format(
            self.__class__.__name__, self.dtstart, self.dtend, len(self))


class SyncRqList(List):
    """ Base cass for *SYNCRQ """
    token = String(10)
    tokenonly = Bool()
    refresh = Bool()
    rejectifmissing = Bool(required=True)

    metadataTags = ['TOKEN', 'TOKENONLY', 'REFRESH', 'REJECTIFMISSING']
    requiredMutexes = [('token', 'tokenonly', 'refresh'), ]

    def __init__(self, token, tokenonly, refresh, rejectifmissing, *members):
        # To validate "choice" args (token/tokenonly/refresh) we stick them
        # into ``requiredMutexes`` and reuse the logic in
        # ``Agregate.validate_kwargs()``
        self.validate_kwargs({'token': token, 'tokenonly': tokenonly,
                              'refresh': refresh})
        self.token = token
        self.tokenonly = tokenonly
        self.refresh = refresh
        self.rejectifmissing = rejectifmissing

        super().__init__(*members)


class SyncRsList(List):
    """ Base cass for *SYNCRS """
    token = String(10, required=True)
    lostsync = Bool()

    metadataTags = ['TOKEN', 'LOSTSYNC']

    def __init__(self, token, lostsync, *members):
        self.token = token
        self.lostsync = lostsync

        super().__init__(*members)
