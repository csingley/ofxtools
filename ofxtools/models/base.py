# coding: utf-8
"""
Bases for OFX model classes to inherit.

``ofxtools.models`` classes correspond to OFX "Aggregates", as defined in
OFX section 1.3.9 - SGML/XML hierarchy nodes that organize data "Elements" ,
but do not themselves contain data.  In XML terminology, OFX "Aggregates" are
XML elements whose only content is other elements; they don't themselves
have text content.

Aggregates may contain other aggregates (which relationship is implemented
by the ``SubAggregate`` and ``List`` classes) and/or data-bearing
"Elements", i.e. leaf nodes, which are defined in ``ofxtools.Types``.

Names of all Aggregate classes must be ALL CAPS, following the convention of
the OFX spec, to be found in the package namespace by
``Aggregate.from_etree()`` which is called by the ``ofxtools.Parser``.
"""


__all__ = ["Aggregate", "SubAggregate", "Unsupported", "ElementList"]


# stdlib imports
import xml.etree.ElementTree as ET
from collections import OrderedDict, ChainMap
from copy import deepcopy
from typing import (
    Any, List, Dict, Tuple, Callable, Sequence, Mapping,
    Union, Optional,
)


# local imports
from ofxtools.Types import Element, InstanceCounterMixin, ListItem, ListElement
import ofxtools.models
from ofxtools.utils import classproperty, pairwise


class Aggregate(list):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML/XML
    parent node that is empty of data text.
    """

    # Validation constraints used by ``validate_args()``.
    # Aggregate MAY have at most child from  `optionalMutexes``
    optionalMutexes: List[List[str]] = []
    # Aggregate MUST contain exactly one child from ``requiredMutexes``
    requiredMutexes: List[List[str]] = []

    def __init__(self, *args, **kwargs):
        """
        Positional args interepreted as list items (of variable #).
        kwargs interpreted as singular sub-elements.
        """
        list.__init__(self)
        self.validate_args(*args, **kwargs)

        for attr in self.spec_no_listitems:
            value = kwargs.pop(attr, None)
            try:
                # If attr is an element (i.e. its class is defined in
                # ``ofxtools.Types``, not defined below as ``Subaggregate``,
                # ``List``, etc.) then its value is type-converted here.
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        self._apply_args(*args)
        self._apply_residual_kwargs(**kwargs)

    @classmethod
    def validate_args(cls, *args, **kwargs) -> None:
        """
        Extra class-level validation constraints from the OFX spec not captured
        by class attribute validators.
        """

        def enforce_count(cls,
                          args: tuple,
                          kwargs: Dict[str, Any],
                          errMsg: str,
                          **extra_kwargs,
                          ):
            assert "mutexes" in extra_kwargs
            assert "predicate" in extra_kwargs

            for mutex in extra_kwargs["mutexes"]:
                count = sum([kwargs.get(i, None) is not None for i in mutex])
                if not extra_kwargs["predicate"](count):
                    kwargs_ = ", ".join(
                        ["{}={}".format(i, kwargs.get(i, None)) for i in mutex]
                    )
                    errFields = {
                        "cls": cls.__name__,
                        "kwargs": kwargs_,
                        "mutex": mutex,
                        "count": count,
                    }
                    raise ValueError(errMsg.format(**errFields))

        enforce_count(cls, args, kwargs,
                      errMsg=("{cls}({kwargs}): must contain at most 1 of "
                              "[{mutex}] (not {count})"),
                      mutexes=cls.optionalMutexes, predicate=lambda x: x <= 1)

        enforce_count(cls, args, kwargs,
                      errMsg=("{cls}({kwargs}): must contain exactly 1 of "
                              "[{mutex}] (not {count})"),
                      mutexes=cls.requiredMutexes, predicate=lambda x: x == 1)

    def _apply_args(self, *args: "Aggregate") -> None:
        # Interpret positional args as contained list items (of variable #)
        for member in args:
            cls_name = member.__class__.__name__.lower()
            if cls_name not in self.listitems:
                msg = "{} can't contain {} as list item: {}"
                raise ValueError(msg.format(self.__class__.__name__,
                                            cls_name, member))
            self.append(member)

    def _apply_residual_kwargs(self, **kwargs) -> None:
        # Check that all kwargs have been consumed
        if kwargs:
            args = {k: v for k, v in kwargs.items() if k in self.listitems}
            if args:
                msg = "{}: pass ListItems as args, not kwargs".format(
                    list(args.keys()))
            else:
                msg = "Aggregate {} does not define {} (spec={})".format(
                    self.__class__.__name__,
                    str(list(kwargs.keys())),
                    str(list(self.spec.keys())),
                )
            raise ValueError(msg)

    @classmethod
    def from_etree(cls, elem: ET.Element) -> "Aggregate":
        """
        Instantiate from ``xml.etree.ElementTree.Element``.

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
        elem = SubClass.groom(elem)

        instance = SubClass._convert(elem)
        return instance

    @classmethod
    def _convert(cls, elem: ET.Element) -> "Aggregate":
        if len(elem) == 0:
            return cls()
        args: List = []
        kwargs: Dict = {}
        specIndices: List = []

        for subelem in elem:
            cls._mapArgs(subelem, args, kwargs, specIndices)

        listitems = cls.listitems
        # Verify that SubElements appear in the order defined by SubClass.spec
        for (idx0, attr0), (idx1, attr1) in pairwise(specIndices):
            # Relative order of ListItems doesn't matter, but position of
            # ListItems relative to non-ListItems (and that of non-ListItems
            # relative to other non-ListItems) does matter.
            if idx1 <= idx0 and (attr0 not in listitems
                                 or attr1 not in listitems):
                msg = "{} SubElements out of order: {}"
                raise ValueError(msg.format(cls.__name__,
                                            [el.tag for el in elem]))
        return cls(*args, **kwargs)

    @classmethod
    def _mapArgs(cls,
                 elem: ET.Element,
                 args: List[Any],
                 kwargs: Dict[Any, Any],
                 specIndices: List[Any],
                 ) -> None:
        spec = list(cls.spec)

        key = elem.tag.lower()
        try:
            idx = spec.index(key)
        except ValueError:
            msg = "{}.spec = {}; does not contain {}"
            raise ValueError(msg.format(cls.__name__, spec, key))

        # If child contains text data, it's an Element; return text data.
        # Otherwise it's an Aggregate - perform type conversion
        if key in cls.unsupported:
            value: Optional[Union[str, Aggregate]] = None
        elif elem.text:
            value = elem.text
        else:
            value = Aggregate.from_etree(elem)

        if key in cls.listitems:
            args.append(value)
        else:
            kwargs[key] = value

        specIndices.append((idx, spec[idx]))

    @staticmethod
    def groom(elem):
        """
        Modify incoming ``ET.Element`` to play nice with our Python schema.

        Default action is to emove extended tags, e.g. INTU.XXX

        Extend in subclass.

        N.B. make sure to perform modifications on a copy.deepcopy(), in order
        to keep the input free of side effects!
        """
        elem = deepcopy(elem)

        for child in set(elem):
            if "." in child.tag:
                elem.remove(child)

        return elem

    def to_etree(self):
        """
        Convert self and children to `ElementTree.Element` hierarchy
        """
        cls = self.__class__
        root = ET.Element(cls.__name__)
        do_list = True  # HACK

        for attr, type_ in self.spec.items():
            if isinstance(type_, (ListItem, ListElement)):
                # HACK - the assumption here is that all ListItems/ListElements
                # occur immediately adjacent to each other in the class
                # definition.  So when you encounter the first one, process
                # all Aggregate contained sequence items, then don't do them
                # again for subsequent ListItems/ListElements.
                if do_list:
                    for member in self:
                        self._listAppend(root, member)
                    do_list = False
            else:
                value = getattr(self, attr)
                if value is None:
                    continue
                elif isinstance(value, Aggregate):
                    child = value.to_etree()
                    #  child = value.ungroom(child)
                    root.append(child)
                else:
                    converter = cls._superdict[attr]
                    text = converter.unconvert(value)
                    ET.SubElement(root, attr.upper()).text = text

        # Hook to modify `ET.ElementTree` after conversion
        return cls.ungroom(root)

    def _listAppend(self, root, member):
        root.append(member.to_etree())

    @classproperty
    @classmethod
    def _superdict(cls) -> Mapping:
        """
        Consolidate cls.__dict__ with that of all superclasses.
        """
        return ChainMap(*[base.__dict__ for base in cls.mro()])

    @staticmethod
    def ungroom(elem: ET.Element) -> ET.Element:
        """
        Reverse groom() when converting back to ElementTree.

        Override in subclass.

        N.B. make sure to perform modifications on a copy.deepcopy(), in order
        to keep the input free of side effects.
        """
        return elem

    @classmethod
    def _ordered_attrs(cls, predicate: Callable) -> OrderedDict:
        """
        Filter class attributes for items matching the given predicate.

        Return them as an OrderedDict in the same order they're declared in the
        class definition.

        N.B. predicate tests *values* of cls._superdict
             (not keys i.e. attribute names)
        """
        match_items = [(k, v) for k, v in cls._superdict.items()
                       if predicate(v)]
        match_items.sort(key=lambda it: it[1]._counter)
        return OrderedDict(match_items)

    @classproperty
    @classmethod
    def spec(cls) -> OrderedDict:
        """
        OrderedDict of all class attributes that are
        Elements/SubAggregates/Unsupported.

        N.B. SubAggregate is a subclass of Element.
        """
        return cls._ordered_attrs(
            lambda v: isinstance(v, (Element, Unsupported)))

    @classproperty
    @classmethod
    def spec_no_listitems(cls) -> OrderedDict:
        """
        OrderedDict of all class attributes that are
        Elements/SubAggregates/Unsupported, excluding ListItems/ListElements
        """
        return cls._ordered_attrs(
            lambda v: isinstance(v, (Element, Unsupported))
            and not isinstance(v, (ListItem, ListElement)))

    @classproperty
    @classmethod
    def elements(cls) -> OrderedDict:
        """
        OrderedDict of all class attributes that are Elements but not
        SubAggregates.
        """
        return cls._ordered_attrs(
            lambda v: isinstance(v, Element) and not isinstance(v,
                                                                SubAggregate)
        )

    @classproperty
    @classmethod
    def subaggregates(cls) -> OrderedDict:
        """
        OrderedDict of all class attributes that are SubAggregates.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, SubAggregate))

    @classproperty
    @classmethod
    def unsupported(cls) -> OrderedDict:
        """
        OrderedDict of all class attributes that are Unsupported.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, Unsupported))

    @classproperty
    @classmethod
    def listitems(cls) -> OrderedDict:
        """
        OrderedDict of all class attributes that are ListItems.
        """
        return cls._ordered_attrs(lambda v: isinstance(v, ListItem))

    @property
    def _spec_repr(self) -> Sequence[Tuple[str, Any]]:
        """
        Sequence of (name, repr()) for each non-empty attribute in the
        class ``_spec`` (see property above).

        Used by __repr__().
        """
        attrs = [
            (attr, repr(getattr(self, attr)))
            for attr, validator in self.spec.items()
            if not isinstance(validator, (ListItem, ListElement))
            and getattr(self, attr) is not None
        ]
        return attrs

    def __hash__(self) -> int:
        """
        HACK - as a subclass of list, List is unhashable, but we need to
        use it as a dict key in Type.Element.{__get__, __set__}
        """
        return object.__hash__(self)

    def __repr__(self) -> str:
        attrs = ["{}={}".format(*attr) for attr in self._spec_repr]
        instance_repr = "{}({})".format(
            self.__class__.__name__, ", ".join(attrs))
        num_list_elements = len(self)
        if num_list_elements != 0:
            instance_repr += ", len={}".format(num_list_elements)
        return "<{}>".format(instance_repr)

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

    def _convert_default(self, value):
        if not isinstance(value, self.type):
            msg = "'{}' is not an instance of {}"
            raise ValueError(msg.format(value, self.type))
        return value

    #  This doesn't get used
    #  def __repr__(self):
    #  return "<{}>".format(self.type.__name__)


class Unsupported(InstanceCounterMixin):
    """
    Null Aggregate/Element - not implemented (yet)
    """

    def __get__(self, instance, type_) -> None:
        pass

    def __set__(self, instance, value) -> None:
        pass

    def __repr__(self) -> str:
        return "<Unsupported>"


class ElementList(Aggregate):
    """
    Aggregate whose sequence contents are ListElements instead of ListItems
    """
    @classproperty
    @classmethod
    def listitems(cls):
        """
        ElementList.listitems returns ListElements instead of ListItems
        """
        return cls._ordered_attrs(lambda v: isinstance(v, ListElement))

    def _apply_args(self, *args):
        # Interpret positional args as contained list items (of variable #)
        assert len(self.listitems) == 1
        converter = list(self.listitems.values())[0]
        for member in args:
            self.append(converter.convert(member))

    def _listAppend(self, root, member):
        assert len(self.listitems) == 1
        spec = list(self.listitems.items())[0]
        attr, converter = spec

        text = converter.unconvert(member)
        ET.SubElement(root, attr.upper()).text = text
