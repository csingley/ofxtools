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
from ofxtools.Types import Element, DateTime, String, Bool, InstanceCounterMixin


class classproperty(property):
    """ Decorator that turns a classmethod into a property """

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class Aggregate:
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML/XML
    parent node that is empty of data text.

    The alternate ``from_etree()`` instance constructor takes an instance of
    ``xml.etree.ElementTree.Element``.
    """

    # Validation constraints used by ``validate_kwargs()``.
    # Sequences of tuples (type str) defining mutually exclusive child tags.

    # Aggregate MAY have at most child from  `optionalMutexes``
    optionalMutexes = []
    # Aggregate MUST contain exactly one child from ``requiredMutexes``
    requiredMutexes = []

    def __init__(self, **kwargs):
        self.validate_kwargs(kwargs)

        # Set instance attributes for all SubAggregates and Elements defined in
        # ``Aggregate.spec`` (i.e. class attributes), defaulting to None if not
        # given by kwargs
        for attr in self.spec:
            value = kwargs.pop(attr, None)
            try:
                # If attr is an element (i.e. its class is defined in
                # ``ofxtools.Types``, not defined below as ``Subaggregate``,
                # ``List``, etc.) then its value is type-converted here.
                # ``Types.Element.__set__()`` calls ``convert()``
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        # Check that all args have been consumed, i.e. we haven't been passed
        # any args that aren't in ``self.spec()``.
        if kwargs:
            msg = "Aggregate {} does not define {} (spec={})".format(
                self.__class__.__name__,
                str(list(kwargs.keys())),
                str(list(self.spec.keys())),
            )
            raise ValueError(msg)

    @classmethod
    def validate_kwargs(cls, kwargs):
        """
        Extra class-level validation constraints from the OFX spec not captured
        by class attribute validators.
        """

        def enforce_count(attr, predicate, errMsg):
            """
            Raise error if the # of non-empty elements of each subsequence
            of ``attr`` doesn't conform to ``predicate``
            """
            for mutex in attr:
                count = sum([kwargs.get(i, None) is not None for i in mutex])
                if not predicate(count):
                    args = ", ".join(
                        ["{}={}".format(i, kwargs.get(i, None)) for i in mutex]
                    )
                    errFields = {
                        "cls": cls.__name__,
                        "args": args,
                        "mutex": mutex,
                        "count": count,
                    }
                    raise ValueError(errMsg.format(**errFields))

        enforce_count(
            cls.optionalMutexes,
            lambda x: x <= 1,
            errMsg="{cls}({args}): must contain at most 1 of [{mutex}] (not {count})",
        )

        enforce_count(
            cls.requiredMutexes,
            lambda x: x == 1,
            errMsg="{cls}({args}): must contain exactly 1 of [{mutex}] (not {count})",
        )

    @classmethod
    def from_etree(cls, elem):
        """
        Instantiate from ``xml.etree.ElementTree.Element`` instead of kwargs.

        Look up `Aggregate`` subclass corresponding to ``Element.tag``;
        parse the Element structure into (args, kwargs) and pass those
        to the subclass __init__().
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
        Extract args from ``ET.Element`` to pass to __init__().

        Generic ``Aggregate`` subclass __init__() accepts only keyword args.
        """
        spec = list(cls.spec)

        def indexOrRaise(attr):
            try:
                return spec.index(attr)
            except ValueError:
                msg = "Aggregate {} does not define {} in spec {}"
                raise ValueError(msg.format(cls.__name__, attr, spec))

        kwargs = {}
        specIndices = []

        for subelem in elem:
            key = subelem.tag.lower()
            # If the child contains text data, the metadata is an Element;
            # return the text data.  Otherwise it's an Aggregate - perform
            # type conversion.
            if key in cls.unsupported:
                value = None
            elif subelem.text:
                value = subelem.text
            else:
                value = Aggregate.from_etree(subelem)

            specIndices.append(indexOrRaise(key))
            # In OFX, child tags may not be repeated (except for list-type
            # Aggregates - see subclass ``List._etree2args()`` below).
            if key in kwargs:
                msg = "{} contains multiple {}"
                raise ValueError(msg.format(cls.__name__, key))
            kwargs[key] = value

        # Verify that SubElements appear in the order defined by the ``spec``.
        if specIndices != sorted(specIndices):
            msg = "{} SubElements out of order: {}"
            raise ValueError(msg.format(cls.__name__, [el.tag for el in elem]))

        return [], kwargs

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
                converter = cls._superdict[spec]
                text = converter.unconvert(value)
                ET.SubElement(root, spec.upper()).text = text
        return root

    @classproperty
    @classmethod
    def _superdict(cls):
        """
        Consolidate cls.__dict__ with that of all superclasses.

        Traverse the method resolution order in reverse so that attributes
        defined on subclass override attributes defined on superclass.
        """
        d = OrderedDict()
        for base in reversed(cls.mro()):
            d.update(base.__dict__)
        return d

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
        Filter class attributes for items matching the given predicate.

        Return them as an OrderedDict in the same order they're declared in the
        class definition.

        N.B. predicate tests *values* of cls._superdict
             (not keys i.e. attribute names)
        """
        match_items = [(k, v) for k, v in cls._superdict.items() if predicate(v)]
        match_items.sort(key=lambda it: it[1]._counter)
        return OrderedDict(match_items)

    @classproperty
    @classmethod
    def spec(cls):
        """
        OrderedDict of all class attributes that are
        Elements/SubAggregates/Unsupported.

        N.B. SubAggregate is a subclass of Element.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, (Element, Unsupported)))

    @classproperty
    @classmethod
    def elements(cls):
        """
        OrderedDict of all class attributes that are Elements but not
        SubAggregates.
        """
        return cls._ordered_attrs(
            lambda v: isinstance(v, Element) and not isinstance(v, SubAggregate)
        )

    @classproperty
    @classmethod
    def subaggregates(cls):
        """
        OrderedDict of all class attributes that are SubAggregates.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, SubAggregate))

    @classproperty
    @classmethod
    def unsupported(cls):
        """
        OrderedDict of all class attributes that are Unsupported.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, Unsupported))

    @property
    def _spec_repr(self):
        """
        Sequence of (name, repr()) for each non-empty attribute in the
        class ``_spec`` (see property above).

        Used by __repr__().
        """
        attrs = [
            (attr, repr(getattr(self, attr)))
            for attr in self.spec
            if getattr(self, attr) is not None
        ]
        return attrs

    def __repr__(self):
        attrs = ["{}={}".format(*attr) for attr in self._spec_repr]
        return "<{}({})>".format(self.__class__.__name__, ", ".join(attrs))

    def __getattr__(self, attr):
        """ Proxy access to attributes of SubAggregates """
        for subaggregate in self.subaggregates:
            subagg = getattr(self, subaggregate)
            try:
                return getattr(subagg, attr)
            except AttributeError:
                continue
        msg = "'{}' object has no attribute '{}'"
        raise AttributeError(msg.format(self.__class__.__name__, attr))


class SubAggregate(Element):
    """
    Aggregate that is a child of this parent Aggregate.

    SubAggregate instances appear only in the model class definitions
    (Aggregate subclasses).  Actual model instances replace these SubAggregate
    instances with the Aggregate instances to which they refer.

    The main job of a SubAggregate is to contribute to the ``spec`` of its
    parent model class.  It also validates ``__init__()`` args via its
    ``convert()`` method.
    """

    def _init(self, *args, **kwargs):
        args = list(args)
        self.type = args.pop(0)
        assert issubclass(self.type, Aggregate)
        super()._init(*args, **kwargs)

    def convert(self, value):
        if not isinstance(value, (self.type, type(None))):
            msg = "'{}' is not an instance of {}"
            raise ValueError(msg.format(value, self.type))

        return super().convert(value)

    def __repr__(self):
        return "<{}>".format(self.type.__name__)


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

    # ``List.metadataTags`` means fixed child entities (in the OFX spec)
    # other than the variable-length sequence of contained ``Aggregates``.
    # Define as sequence of OFX tags (type str) corresponding to __init__()
    # positional args - order is significant.
    # Used by ``_etree2args()`` to parse args.
    metadataTags = []
    # Sequence of OFX tags (type str) allowed to occur as contained
    # ``Aggregates``.
    # Used by ``__init__()`` to validate args.
    dataTags = []

    def __init__(self, *args):
        list.__init__(self)

        # ``List.__init__()`` only accepts positional args, not kwargs.
        # Parse the first n args as fixed-position metadata (with position
        # corresponding to the order they appear in ``metadataTags``.
        metadataTags = self.metadataTags
        metadataLen = len(metadataTags)
        if len(args) < metadataLen:
            msg = "{}.__init__() needs positional args for each of {}"
            raise ValueError(msg.format(self.__class__.__name__, self.metadataTags))

        for i, tag in enumerate(metadataTags):
            setattr(self, tag.lower(), args[i])

        # In the base ``Aggregate`` class, ``requiredMutexes`` are validated
        # by ``validate_kwargs()``.  ``List`` subclasses don't accept kwargs,
        # so pack up our args in a dict and reuse the function.
        fake_kwargs = {}
        for mutexes in self.requiredMutexes:
            fake_kwargs.update(({mx: getattr(self, mx) for mx in mutexes}))
        self.validate_kwargs(fake_kwargs)

        # Remaining args as variable-length contained data.
        for member in args[metadataLen:]:
            cls_name = member.__class__.__name__
            if cls_name not in self.dataTags:
                msg = "{} can't contain {} as List data: {}"
                raise ValueError(msg.format(self.__class__.__name__, cls_name, member))
            self.append(member)

    @classmethod
    def _etree2args(cls, elem):
        """
        Extract args to pass to __init__() from ``ET.Element``.

        ``List.__init__()`` accepts only positional args
        (unlike ``Aggregate.__init__()``)
        """
        # Remove List metadata and pass as positional args before list members
        def find_metadata(tag):
            child = elem.find(tag)
            if child is not None:
                assert child not in cls.unsupported
                elem.remove(child)
                # If the child contains text data, the metadata is an Element;
                # return the text data.  Otherwise it's an Aggregate - perform
                # type conversion.
                text = child.text
                if text:
                    child = text
                else:
                    child = Aggregate.from_etree(child)
            return child

        args = [find_metadata(tag) for tag in cls.metadataTags]

        # Append list members as variable-length positional args
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
                converter = cls._superdict[spec]
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
        return "<{} len={}>".format(self.__class__.__name__, len(self))
