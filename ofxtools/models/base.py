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
from collections import ChainMap
from copy import deepcopy
from typing import Any, List, Dict, Tuple, Callable, Sequence, Mapping, Union, Optional
import logging


# local imports
from ofxtools.Types import Element, ListItem, ListElement
import ofxtools.models
from ofxtools.utils import classproperty, pairwise, partition


logger = logging.getLogger(__name__)


class OFXAggregateError(ValueError):
    """ Base class for errors in this module """


class OFXSpecError(OFXAggregateError):
    """ Violation of the OFX specification """


class Aggregate(list):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML/XML
    parent node that is empty of data text.
    """

    # Validation constraints used by ``validate_args()``.

    # Aggregate MAY have at most child from  `optionalMutexes``
    optionalMutexes: Sequence[Sequence[str]] = []

    # Aggregate MUST contain exactly one child from ``requiredMutexes``
    requiredMutexes: Sequence[Sequence[str]] = []

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
            except ValueError as exc:
                cls = self.__class__.__name__
                msg = exc.args[0]
                raise type(exc)(f"Can't set {cls}.{attr} to {value}: {msg}")

        self._apply_args(*args)
        self._apply_residual_kwargs(**kwargs)

    @classmethod
    def validate_args(cls, *args, **kwargs) -> None:
        """
        Extra class-level validation constraints from the OFX spec not captured
        by class attribute validators.
        """

        def enforce_count(
            cls,
            kwargs: Dict[str, Any],
            errMsg: str,
            mutexes: Sequence[Sequence[str]],
            predicate: Callable[[int], bool],
        ) -> None:

            for mutex in mutexes:
                count = sum([kwargs.get(m, None) is not None for m in mutex])
                if not predicate(count):
                    kwargs_ = ", ".join(
                        ["{}={}".format(m, kwargs.get(m, None)) for m in mutex]
                    )
                    errFields = {
                        "cls": cls.__name__,
                        "kwargs": kwargs_,
                        "mutex": mutex,
                        "count": count,
                    }
                    raise OFXSpecError(errMsg.format(**errFields))

        enforce_count(
            cls,
            kwargs,
            errMsg="{cls}({kwargs}): must contain at most 1 of [{mutex}] (not {count})",
            mutexes=cls.optionalMutexes,
            predicate=lambda x: x <= 1,
        )

        enforce_count(
            cls,
            kwargs,
            errMsg="{cls}({kwargs}): must contain exactly 1 of [{mutex}] (not {count})",
            mutexes=cls.requiredMutexes,
            predicate=lambda x: x == 1,
        )

    def _apply_args(self, *args: "Aggregate") -> None:
        # Interpret positional args as contained list items (of variable #)
        for member in args:
            arg = member.__class__.__name__.lower()
            if arg not in self.listitems:
                clsnm = self.__class__.__name__
                msg = f"{clsnm} can't contain {arg} as list item: {member}"
                raise TypeError(msg)
            self.append(member)

    def _apply_residual_kwargs(self, **kwargs) -> None:
        # Check that all kwargs have been consumed
        if kwargs:
            args = [k for k in kwargs.keys() if k in self.listitems]
            if args:
                msg = f"{args}: pass ListItems as args, not kwargs"
                raise SyntaxError(msg)
            else:
                cls = self.__class__.__name__
                kw = str(list(kwargs.keys()))
                spc = str(list(self.spec.keys()))
                msg = f"Aggregate {cls} does not define {kw} (spec={spc})"
                raise OFXSpecError(msg)

    @classmethod
    def from_etree(cls, elem: ET.Element) -> "Aggregate":
        """
        Instantiate from ``xml.etree.ElementTree.Element``.

        Look up `Aggregate`` subclass corresponding to ``ET.Element.tag``
        and pass to the subclass ``_convert()``, which actually perfoms the
        instantiation.
        """
        if not isinstance(elem, ET.Element):
            msg = f"Bad type {type(elem)} - should be xml.etree.ElementTree.Element"
            raise TypeError(msg)
        try:
            SubClass = getattr(ofxtools.models, elem.tag)
        except AttributeError:
            raise OFXSpecError(f"ofxtools.models doesn't define {elem.tag}")

        logger.info(f"Converting <{elem.tag}> to {SubClass.__name__}")
        instance = SubClass._convert(elem)
        return instance

    @classmethod
    def _convert(cls, elem: ET.Element) -> "Aggregate":
        """
        Instantiate from ``xml.etree.ElementTree.Element``.

        N.B. this method most be called on the appropriate subclass,
        not the ``Aggregate`` base class.
        """
        if len(elem) == 0:
            return cls()

        # Hook to modify incoming ``ET.Element`` before conversion
        elem = cls.groom(elem)

        spec = list(cls.spec)
        listitems = cls.listitems

        def extractArgs(elem: ET.Element) -> Tuple[Tuple[str, Any], Tuple[int, Any]]:
            """
            Transform input ET.Element into attribute name/ value pairs ready
            to pass to Aggregate.__init__(), as well as a sequence check.
            """
            key = elem.tag.lower()
            try:
                index = spec.index(key)
            except ValueError:
                clsnm = cls.__name__
                raise OFXSpecError(f"{clsnm}.spec = {spec}; does not contain {key}")

            if key in cls.unsupported:
                value: Optional[Union[str, Aggregate]] = None
            elif elem.text:
                # Element - extract raw text string; it will be type converted
                # when used to set an Aggregate class attribute
                value = elem.text
            else:
                # Aggregate - perform type conversion
                value = Aggregate.from_etree(elem)

            return (key, value), (index, key in listitems)

        def outOfOrder(index0: Tuple[int, bool], index1: Tuple[int, bool]) -> bool:
            """
            Do SubElements appear not in the order defined by SubClass.spec?
            """
            idx0, isListItem0 = index0
            idx1, isListItem1 = index1
            # Relative order of ListItems doesn't matter, but position of
            # ListItems relative to non-ListItems (and that of non-ListItems
            # relative to other non-ListItems) does matter.
            return idx1 <= idx0 and (not isListItem0 or not isListItem1)

        args_, specIndices = zip(*[extractArgs(subelem) for subelem in elem])
        clsnm = cls.__name__
        logger.debug(f"Args to instantiate {clsnm}: {args_}")
        if any(
            [outOfOrder(index0, index1) for index0, index1 in pairwise(specIndices)]
        ):
            subels = [el.tag for el in elem]
            raise OFXSpecError(f"{clsnm} SubElements out of order: {subels}")
        kwargs, args = partition(lambda p: p[0] in listitems, args_)
        return cls(*[arg[1] for arg in args], **dict(kwargs))

    @staticmethod
    def groom(elem: ET.Element) -> ET.Element:
        """
        Modify incoming ``ET.Element`` to play nice with our Python schema.

        Default action is to remove extended tags, e.g. INTU.XXX

        Extend in subclass.

        N.B. make sure to perform modifications on a copy.deepcopy(), in order
        to keep the input free of side effects!
        """
        elem = deepcopy(elem)

        for child in set(elem):
            if "." in child.tag:
                logger.debug(f"Removing extended tag <{child.tag}>")
                elem.remove(child)

        return elem

    def to_etree(self) -> ET.Element:
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
                    root.append(child)
                else:
                    converter = cls._superdict[attr]
                    text = converter.unconvert(value)
                    ET.SubElement(root, attr.upper()).text = text

        # Hook to modify `ET.ElementTree` after conversion
        return cls.ungroom(root)

    def _listAppend(self, root: ET.Element, member) -> None:
        root.append(member.to_etree())

    @staticmethod
    def ungroom(elem: ET.Element) -> ET.Element:
        """
        Reverse groom() when converting back to ElementTree.

        Override in subclass.

        N.B. make sure to perform modifications on a copy.deepcopy(), in order
        to keep the input free of side effects.
        """
        return elem

    @classproperty
    @classmethod
    def _superdict(cls) -> Mapping[str, Any]:
        """
        Consolidate cls.__dict__ with that of all superclasses.
        """
        return ChainMap(*[base.__dict__ for base in cls.mro()])

    @classmethod
    def _filter_attrs(cls, predicate: Callable) -> Mapping[str, Any]:
        """
        Filter class attributes for items matching the given predicate.

        Return them as a mapping in the same order they're declared in the
        class definition.

        N.B. predicate tests *values* of cls._superdict
             (not keys i.e. attribute names)
        """
        return {k: v for k, v in cls._superdict.items() if predicate(v)}

    @classproperty
    @classmethod
    def spec(cls) -> Mapping[str, Union[Element, "Unsupported"]]:
        """
        Mapping of all class attributes that are Elements/SubAggregates/Unsupported.

        N.B. SubAggregate is a subclass of Element.
        """
        return cls._filter_attrs(lambda v: isinstance(v, (Element, Unsupported)))

    @classproperty
    @classmethod
    def spec_no_listitems(cls) -> Mapping[str, Union[Element, "Unsupported"]]:
        """
        Mapping of all class attributes that are
        Elements/SubAggregates/Unsupported, excluding ListItems/ListElements
        """
        return cls._filter_attrs(
            lambda v: isinstance(v, (Element, Unsupported))
            and not isinstance(v, (ListItem, ListElement))
        )

    @classproperty
    @classmethod
    def elements(cls) -> Mapping[str, Element]:
        """
        Mapping of all class attributes that are Elements but not SubAggregates.
        """
        return cls._filter_attrs(
            lambda v: isinstance(v, Element) and not isinstance(v, SubAggregate)
        )

    @classproperty
    @classmethod
    def subaggregates(cls) -> Mapping[str, "SubAggregate"]:
        """
        Mapping of all class attributes that are SubAggregates.
        """
        return cls._filter_attrs(lambda v: isinstance(v, SubAggregate))

    @classproperty
    @classmethod
    def unsupported(cls) -> Mapping[str, "Unsupported"]:
        """
        Mapping of all class attributes that are Unsupported.
        """
        return cls._filter_attrs(lambda v: isinstance(v, Unsupported))

    @classproperty
    @classmethod
    def listitems(cls) -> Mapping[str, ListItem]:
        """
        Mapping of all class attributes that are ListItems.
        """
        return cls._filter_attrs(lambda v: isinstance(v, ListItem))

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
        instance_repr = "{}({})".format(self.__class__.__name__, ", ".join(attrs))
        num_list_elements = len(self)
        if num_list_elements != 0:
            instance_repr += ", len={}".format(num_list_elements)
        return "<{}>".format(instance_repr)

    def __getattr__(self, attr: str):
        """ Proxy access to attributes of SubAggregates """
        for subaggregate in self.subaggregates:
            subagg = getattr(self, subaggregate)
            try:
                return getattr(subagg, attr)
            except AttributeError:
                continue
        cls = self.__class__.__name__
        raise AttributeError(f"'{cls}' object has no attribute '{attr}'")


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
            raise TypeError(f"'{value}' is not an instance of {self.type}")
        return value

    #  This doesn't get used
    #  def __repr__(self):
    #  return "<{}>".format(self.type.__name__)


class Unsupported:
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
    def listitems(cls) -> Mapping[str, ListElement]:
        """
        ElementList.listitems returns ListElements instead of ListItems
        """
        return cls._filter_attrs(lambda v: isinstance(v, ListElement))

    def _apply_args(self, *args) -> None:
        # Interpret positional args as contained list items (of variable #)
        assert len(self.listitems) == 1
        converter = list(self.listitems.values())[0]
        for member in args:
            self.append(converter.convert(member))

    def _listAppend(self, root: ET.Element, member) -> None:
        assert len(self.listitems) == 1
        spec = list(self.listitems.items())[0]
        attr, converter = spec

        text = converter.unconvert(member)
        ET.SubElement(root, attr.upper()).text = text
