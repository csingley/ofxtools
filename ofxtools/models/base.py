# coding: utf-8
"""
Bases for OFX model classes to inherit.

``ofxtools.models`` classes correspond to OFX "Aggregates", as defined in
OFX section 1.3.9 - SGML/XML hierarchy nodes that organize data "Elements" ,
but do not themselves contain data.  In XML terminology, OFX "Aggregates" are
XML elements whose only content is other elements; they don't themselves
have text content.

Aggregates may contain other aggregates (which relationship is implemented
by the ``Types.SubAggregate`` and ``ListAggregate`` classes) and/or data-bearing
"Elements", i.e. leaf nodes, which are defined in ``ofxtools.Types``.

Names of all Aggregate classes must be ALL CAPS, following the convention of
the OFX spec, to be found in the package namespace by
``Aggregate.from_etree()`` which is called by the ``ofxtools.Parser``.
"""


__all__ = ["Aggregate", "ElementList"]


# stdlib imports
import xml.etree.ElementTree as ET
from copy import deepcopy
import functools
from typing import (
    Any,
    Dict,
    Tuple,
    Callable,
    Sequence,
    Mapping,
    Union,
    Optional,
    ChainMap,
)
import logging
import warnings


# local imports
from ofxtools import Types

import ofxtools.models
from ofxtools.utils import classproperty


logger = logging.getLogger(__name__)


class OFXAggregateError(ValueError):
    """Base class for errors in this module."""


class OFXSpecError(OFXAggregateError):
    """Violation of the OFX specification."""


class OFXAggregateWarning(UserWarning):
    """Base class for warnings in this module."""


class UnknownTagWarning(OFXAggregateWarning):
    """Type conversion fails because Aggregate tag is unrecognized.

    OFXv1 Section 2.3.1:

        Open Financial Exchange is not completely SGML-compliant because the
        specification allows unrecognized tags to be present. Clients and servers must
        skip over the unrecognized tags. That is, if a client or server does not
        recognize <XYZ>, it must ignore the tag and its enclosed data.
    """


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

        for attr in self.spec_no_listaggregates:
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

    def _apply_args(self, *args) -> None:
        # Interpret positional args as contained list items/elements (of variable #)
        clsnm = self.__class__.__name__

        for member in args:
            if isinstance(member, Aggregate):
                # ListAggregate - validate type against spec
                arg = member.__class__.__name__.lower()
                if arg not in self.listaggregates:
                    msg = f"{clsnm} can't contain {arg} as list item: {member}"
                    raise TypeError(msg)
            else:
                # ListElement
                # FIXME validation
                if type(member) is not str:
                    msg = (
                        f"{clsnm} can only contain str as list element, "
                        f"not {member!r}"
                    )
                    raise TypeError(msg)
            self.append(member)

    def _apply_residual_kwargs(self, **kwargs) -> None:
        # Check that all kwargs have been consumed
        if kwargs:
            args = [
                k
                for k in kwargs.keys()
                if k in self.listaggregates or k in self.listelements
            ]
            if args:
                msg = f"{args}: pass list members as args, not kwargs"
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
        """Instantiate from ``xml.etree.ElementTree.Element``.

        N.B. this method must be called on the appropriate subclass,
        not the ``Aggregate`` base class.
        """
        if len(elem) == 0:
            return cls()

        # Hook to modify incoming ``ET.Element`` before conversion
        elem = cls.groom(elem)

        clsnm = cls.__name__
        spec = list(cls.spec)
        listaggregates = cls.listaggregates
        listelements = cls.listelements

        #  Type alias - accumulator for functools.reduce()
        Accum = Tuple[list, dict, int, bool]
        " args, kwargs, previous attr index within spec, previous attr is list member? "

        def update_args(accum: Accum, elem: ET.Element) -> Accum:
            """Extend ``functools.reduce()`` accumulator with parsed ``ET.Element``
            value (either OFX `aggregate` or OFX 'element').

            List members are stored as positional args (i.e. list); everything
            else is stored as keyword args (i.e. dict).

            Check index within the ``Aggregate.spec`` sequence against previous
            ``ET.Element`` and return sequencing info for current ``ET.Element``
            to be used in the next iteration.
            """
            args, kwargs, prev_index, prev_is_listmember = accum
            attrname = elem.tag.lower()

            #  OFX messages have a sequence order defined by the spec.  This order maps
            #  to the order of class attributes defined by ``Aggregate`` subclasses.
            #  Cf. discussion of ordering above in the docstring for ``_filter_attrs()``.
            #
            #  Class attributes defined as list members (i.e. ListAggregate / ListElement,
            #  identified as "one or more" or "zero or more" in the OFX spec) may
            #  occur in any order, so we don't validate the relative order of list
            #  members.  Other than, we require that the index of an attribute within
            #  the ``Aggregate.spec`` sequence must increase monotonically.
            try:
                index = spec.index(attrname)
            except ValueError:
                #  raise OFXSpecError(f"{clsnm}.spec = {spec}; doesn't contain {attrname}")
                msg = (
                    f"While parsing {clsnm}, encountered unknown tag {elem.tag}; "
                    "skipping."
                )
                warnings.warn(msg, category=UnknownTagWarning)
                return accum

            is_listmember = attrname in listaggregates or attrname in listelements
            if index <= prev_index and not (is_listmember and prev_is_listmember):
                msg = (
                    f"Elements out of order: According to the class spec for {clsnm}, "
                    f"{attrname.upper()} should occur before "
                    f"{spec[prev_index].upper()}, not after it."
                )
                raise OFXSpecError(msg)

            # Parse attribute value
            if attrname in cls.unsupported:
                value: Optional[Union[str, Aggregate]] = None
            elif elem.text:
                # Element - extract as string; value will be type-converted upon
                # instance initialization by ``ofxtools.Types.Element.__set__()``.
                value = elem.text
            else:
                # Aggregate - recurse
                value = Aggregate.from_etree(elem)

            # Append attr value to args (list members) or kwargs (everything else)
            if is_listmember:
                args.append(value)
            else:
                if attrname in kwargs:
                    raise OFXSpecError
                kwargs[attrname] = value

            return args, kwargs, index, is_listmember

        #  ElementTree API: child Elements stored as a sequence, accessible
        #  by iterating over the parent Element.
        #  https://effbot.org/zone/pythondoc-elementtree-ElementTree.htm#elementtree.ElementTree._ElementInterface-class
        initial: Accum = ([], {}, -1, False)
        args, kwargs = functools.reduce(update_args, elem, initial)[:2]
        return cls(*args, **kwargs)

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
            if isinstance(type_, (Types.ListAggregate, Types.ListElement)):
                # HACK - the assumption here is that all list members
                # occur immediately adjacent to each other in the class
                # definition.  So when you encounter the first one, process
                # all Aggregate contained sequence items, then don't do them
                # again for subsequent list members.
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
        Consolidate ``cls.__dict__`` with that of all superclasses.

        Ordering is significant for OFX messages, which maps to significant ordering
        of class attributes of ``ofxtools.models.base.Aggregate`` subclasses.

        That ordering is implemented by combining `PEP 520`_ (which was implemented
        as of Python 3.6), `collections.ChainMap`_, and Python's `inheritance chain`_
        (i.e. the MRO).

        PEP 520 guarantees that each class's ``__dict__`` preserves the order in which
        its attributes and methods were defined.  ``ChainMap`` searches its list of
        mappings from left to right.  By feeding a class's MRO into ``ChainMap``, we
        get an ordering where attributes defined on subclasses override those defined
        on the parent, preserving the order of the class definition in each case.

        .. _PEP 520: https://www.python.org/dev/peps/pep-0520/
        .. _collections.ChainMap: https://docs.python.org/3/library/collections.html#collections.ChainMap
        .. _inheritance order: https://www.python.org/download/releases/2.3/mro/
        """
        return ChainMap(*[base.__dict__ for base in cls.mro()])

    @classmethod
    def _filter_attrs(cls, predicate: Callable) -> Mapping[str, Any]:
        """
        Filter class attributes for items matching the given predicate.

        Cf. discussion of ordering above in the docstring for ``_superdict()``.

        In the following example, `_filter_attrs()` always returns a mapping
        whose keys are ordered as ('foo', 'bar', 'baz'), with subclass values
        overriding values defined on the base class.

        >>> class Base(Aggregate):
        ...     foo = 1
        ...     bar = 2
        ...
        >>> class Sub(Base):
        ...     bar = 3
        ...     baz = 4
        ...
        >>> Sub._filter_attrs(lambda v: isinstance(v, int))
        {'foo': 1, 'bar': 3, 'baz': 4}

        N.B. `predicate` tests *values* of cls._superdict
             (not keys i.e. attribute names)
        """
        return {k: v for k, v in cls._superdict.items() if predicate(v)}

    @classproperty
    @classmethod
    def spec(cls) -> Mapping[str, Union[Types.Element, Types.Unsupported]]:
        """
        Mapping of all class attributes that are Elements/SubAggregates/Unsupported.

        Cf. discussion of ordering above in the docstring for ``_filter_attrs()``.

        N.B. Types.SubAggregate is a subclass of Element.
        """
        return cls._filter_attrs(
            lambda v: isinstance(v, (Types.Element, Types.Unsupported))
        )

    @classproperty
    @classmethod
    def spec_no_listaggregates(
        cls,
    ) -> Mapping[str, Union[Types.Element, Types.Unsupported]]:
        """
        Mapping of all class attributes that are
        Elements/SubAggregates/Unsupported, excluding ListAggregates/ListElements.
        """
        return cls._filter_attrs(
            lambda v: isinstance(v, (Types.Element, Types.Unsupported))
            and not isinstance(v, (Types.ListAggregate, Types.ListElement))
        )

    @classproperty
    @classmethod
    def elements(cls) -> Mapping[str, Types.Element]:
        """
        Mapping of all class attributes that are Elements but not SubAggregates.

        N.B. Types.SubAggregate is a subclass of Element.
        """
        return cls._filter_attrs(
            lambda v: isinstance(v, Types.Element)
            and not isinstance(v, Types.SubAggregate)
        )

    @classproperty
    @classmethod
    def subaggregates(cls) -> Mapping[str, Types.SubAggregate]:
        """
        Mapping of all class attributes that are SubAggregates.
        """
        return cls._filter_attrs(lambda v: isinstance(v, Types.SubAggregate))

    @classproperty
    @classmethod
    def unsupported(cls) -> Mapping[str, Types.Unsupported]:
        """
        Mapping of all class attributes that are Unsupported.
        """
        return cls._filter_attrs(lambda v: isinstance(v, Types.Unsupported))

    @classproperty
    @classmethod
    def listaggregates(cls) -> Mapping[str, Types.ListAggregate]:
        """
        Mapping of all class attributes that are ListAggregates.
        """
        return cls._filter_attrs(lambda v: isinstance(v, Types.ListAggregate))

    @classproperty
    @classmethod
    def listelements(cls) -> Mapping[str, Types.ListAggregate]:
        """
        Mapping of all class attributes that are ListElements.
        """
        return cls._filter_attrs(lambda v: isinstance(v, Types.ListElement))

    @property
    def _spec_repr(self) -> Sequence[Tuple[str, Any]]:
        """
        Sequence of (name, repr()) for each non-empty attribute in the
        class ``spec`` (see property above).

        Used by __repr__().
        """
        # FIXME - this comprehension is a good use case for the PEP 572
        # "walrus operator" provided in Python 3.8.
        attrs = [
            (attr, repr(getattr(self, attr)))
            for attr in self.spec_no_listaggregates.keys()
            if getattr(self, attr) is not None
        ]
        return attrs

    def __hash__(self) -> int:  # type: ignore
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
        """Proxy access to attributes of SubAggregates"""
        for subaggregate in self.subaggregates:
            subagg = getattr(self, subaggregate)
            try:
                return getattr(subagg, attr)
            except AttributeError:
                continue
        cls = self.__class__.__name__
        raise AttributeError(f"'{cls}' object has no attribute '{attr}'")


class ElementList(Aggregate):
    """
    Aggregate whose sequence contents are ListElements instead of ListAggregates
    """

    @classproperty
    @classmethod
    def listaggregates(cls) -> Mapping[str, Types.ListElement]:
        """
        ElementList.listaggregates returns ListElements instead of ListAggregates
        """
        return cls._filter_attrs(lambda v: isinstance(v, Types.ListElement))

    def _apply_args(self, *args) -> None:
        # Interpret positional args as contained list items (of variable #)
        assert len(self.listaggregates) == 1
        converter = list(self.listaggregates.values())[0]
        for member in args:
            self.append(converter.convert(member))

    def _listAppend(self, root: ET.Element, member) -> None:
        assert len(self.listaggregates) == 1
        spec = list(self.listaggregates.items())[0]
        attr, converter = spec

        text = converter.unconvert(member)
        ET.SubElement(root, attr.upper()).text = text
