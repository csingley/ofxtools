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

from __future__ import annotations

__all__ = ["Aggregate", "ElementList"]


# stdlib imports
import logging
import warnings
import xml.etree.ElementTree as ET
from collections import ChainMap
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from typing import (
    Any,
)

import ofxtools.models

# local imports
from ofxtools import Types

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


class PrivateTagWarning(OFXAggregateWarning):
    """An OFX private extension tag (containing a period) was encountered and skipped.

    OFX Section 2.7.1 Private Tag Extension:

        All tag names that do not contain a period (.) are reserved for use in
        future versions of the Open Financial Exchange specification. A period in
        a tag name indicates a private tag extension.
    """


class Aggregate(list[Any]):
    """
    Base class for OFX aggregates — SGML/XML parent nodes that contain other
    elements but no direct text data.

    Each concrete subclass corresponds to one OFX aggregate tag (named in ALL
    CAPS per the spec).  Class attributes are either ``Types.Element``
    descriptors (leaf data nodes) or ``Types.SubAggregate`` /
    ``Types.ListAggregate`` descriptors (nested aggregate references).

    ``Aggregate`` subclasses ``list`` to hold variable-count child aggregates
    declared with ``ListAggregate``; singular children declared with
    ``SubAggregate`` are stored as instance attributes instead.

    Use ``Aggregate.from_etree()`` to construct instances from parsed XML, or
    instantiate directly by passing element values as keyword arguments and
    list-aggregate items as positional arguments.

    Class-level mutual-exclusion constraints from the OFX spec are expressed
    via ``requiredMutexes`` and ``optionalMutexes``.
    """

    # Computed by __init_subclass__ and bootstrapped for base classes at module end
    _superdict: Mapping[str, Any]
    spec: Mapping[str, Any]
    spec_no_listaggregates: Mapping[str, Any]
    elements: Mapping[str, Any]
    subaggregates: Mapping[str, Any]
    unsupported: Mapping[str, Any]
    listaggregates: Mapping[str, Any]
    listelements: Mapping[str, Any]

    # Validation constraints used by ``validate_args()``.

    # Aggregate MAY have at most child from  `optionalMutexes``
    optionalMutexes: Sequence[Sequence[str]] = []

    # Aggregate MUST contain exactly one child from ``requiredMutexes``
    requiredMutexes: Sequence[Sequence[str]] = []

    def __init__(self, *args: object, **kwargs: object) -> None:
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
    def validate_args(cls, *args: object, **kwargs: object) -> None:
        """
        Extra class-level validation constraints from the OFX spec not captured
        by class attribute validators.
        """

        def enforce_count(
            cls: type,
            kwargs: dict[str, Any],
            errMsg: str,
            mutexes: Sequence[Sequence[str]],
            predicate: Callable[[int], bool],
        ) -> None:
            for mutex in mutexes:
                count = sum(kwargs.get(m, None) is not None for m in mutex)
                if not predicate(count):
                    kwargs_ = ", ".join([f"{m}={kwargs.get(m, None)}" for m in mutex])
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

    def _apply_args(self, *args: object) -> None:
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
                # Non-Aggregate positional args are only valid for ElementList
                # subclasses, which override _apply_args entirely. Reaching
                # here means a class has ListElement attributes but doesn't
                # inherit from ElementList — a model definition error.
                raise TypeError(
                    f"{clsnm}: non-Aggregate list member {member!r}; "
                    "classes with ListElement attributes must subclass ElementList"
                )
            self.append(member)

    def _apply_residual_kwargs(self, **kwargs: object) -> None:
        # Check that all kwargs have been consumed
        if kwargs:
            args = [
                k for k in kwargs if k in self.listaggregates or k in self.listelements
            ]
            if args:
                msg = f"{args}: pass list members as args, not kwargs"
                raise SyntaxError(msg)
            else:
                cls = self.__class__.__name__
                kw = str(list(kwargs))
                spc = str(list(self.spec))
                msg = f"Aggregate {cls} does not define {kw} (spec={spc})"
                raise OFXSpecError(msg)

    @classmethod
    def from_etree(cls, elem: ET.Element) -> Aggregate:
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
        return instance  # type: ignore[no-any-return]

    @classmethod
    def _convert(cls, elem: ET.Element) -> Aggregate:
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

        #  OFX messages have a sequence order defined by the spec.  This order maps
        #  to the order of class attributes defined by ``Aggregate`` subclasses.
        #
        #  Class attributes defined as list members (i.e. ListAggregate / ListElement,
        #  identified as "one or more" or "zero or more" in the OFX spec) may
        #  occur in any order, so we don't validate the relative order of list
        #  members.  Otherwise, we require that the index of an attribute within
        #  the ``Aggregate.spec`` sequence must increase monotonically.
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        prev_index = -1
        prev_is_listmember = False

        for child in elem:
            attrname = child.tag.lower()

            try:
                index = spec.index(attrname)
            except ValueError:
                warnings.warn(
                    f"While parsing {clsnm}, encountered unknown tag {child.tag}; skipping.",
                    category=UnknownTagWarning,
                )
                continue

            is_listmember = attrname in listaggregates or attrname in listelements
            if index <= prev_index and not (is_listmember and prev_is_listmember):
                raise OFXSpecError(
                    f"Elements out of order: According to the class spec for {clsnm}, "
                    f"{attrname.upper()} should occur before "
                    f"{spec[prev_index].upper()}, not after it."
                )

            # Parse attribute value
            if attrname in cls.unsupported:
                value: str | Aggregate | None = None
            elif attrname not in cls.subaggregates:
                # Element - extract as string; type conversion happens in
                # ``ofxtools.Types.Element.__set__()`` during __init__.
                # Use the class spec (not elem.text) to discriminate text
                # elements from aggregates so empty elements (<MEMO></MEMO>
                # or <MEMO/>) are handled correctly.
                value = child.text
            else:
                # Aggregate - recurse
                value = Aggregate.from_etree(child)

            if is_listmember:
                args.append(value)
            else:
                if attrname in kwargs:
                    raise OFXSpecError(f"Duplicate element <{child.tag}> in {clsnm}")
                kwargs[attrname] = value

            prev_index = index
            prev_is_listmember = is_listmember

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
                warnings.warn(
                    f"Encountered private extension tag <{child.tag}>; skipping.",
                    category=PrivateTagWarning,
                )
                elem.remove(child)

        return elem

    def to_etree(self) -> ET.Element:
        """
        Convert self and children to `ElementTree.Element` hierarchy
        """
        cls = self.__class__
        root = ET.Element(cls.__name__)
        list_processed = False

        for attr, type_ in self.spec.items():
            if isinstance(type_, (Types.ListAggregate, Types.ListElement)):
                # All list members are assumed to be contiguous in the class
                # definition. Process all contained sequence items on first
                # encounter; skip for subsequent list attrs of the same class.
                if not list_processed:
                    for member in self:
                        self._listAppend(root, member)
                    list_processed = True
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

    def _listAppend(self, root: ET.Element, member: Any) -> None:
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

    @classmethod
    def _init_class_attrs(cls) -> None:
        """
        Compute and cache per-class OFX field mappings.

        Called once at class definition time (via ``__init_subclass__``) rather
        than recomputing on every attribute access.  Ordering is significant for
        OFX messages and is preserved by combining PEP 520 insertion-order dicts,
        ``ChainMap``, and Python's MRO.
        """
        # MappingProxyType (from type.__dict__) is read-only; ChainMap stubs
        # require MutableMapping but only mutates the first map at runtime.
        superdict: Mapping[str, Any] = ChainMap(*[base.__dict__ for base in cls.mro()])  # type: ignore[arg-type]
        cls._superdict = superdict
        cls.spec = {k: v for k, v in superdict.items() if isinstance(v, Types.Element)}
        cls.spec_no_listaggregates = {
            k: v
            for k, v in superdict.items()
            if isinstance(v, Types.Element)
            and not isinstance(v, (Types.ListAggregate, Types.ListElement))
        }
        cls.elements = {
            k: v
            for k, v in superdict.items()
            if isinstance(v, Types.Element)
            and not isinstance(v, (Types.SubAggregate, Types.Unsupported))
        }
        cls.subaggregates = {
            k: v for k, v in superdict.items() if isinstance(v, Types.SubAggregate)
        }
        cls.unsupported = {
            k: v for k, v in superdict.items() if isinstance(v, Types.Unsupported)
        }
        cls.listaggregates = {
            k: v for k, v in superdict.items() if isinstance(v, Types.ListAggregate)
        }
        cls.listelements = {
            k: v for k, v in superdict.items() if isinstance(v, Types.ListElement)
        }

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._init_class_attrs()

    @property
    def _spec_repr(self) -> list[tuple[str, str]]:
        """
        Sequence of (name, repr()) for each non-empty attribute in the
        class ``spec`` (see property above).

        Used by __repr__().
        """
        return [
            (attr, repr(v))
            for attr in self.spec_no_listaggregates
            if (v := getattr(self, attr)) is not None
        ]

    def __hash__(self) -> int:  # type: ignore[override]
        """
        Aggregate subclasses list, so it inherits list's __hash__ = None.
        We need instances to be hashable so they can serve as descriptor
        keys in Types.Element.__get__/__set__.
        """
        return object.__hash__(self)

    def __repr__(self) -> str:
        attrs = [f"{k}={v}" for k, v in self._spec_repr]
        instance_repr = f"{self.__class__.__name__}({', '.join(attrs)})"
        num_list_elements = len(self)
        if num_list_elements != 0:
            instance_repr += f", len={num_list_elements}"
        return f"<{instance_repr}>"

    def __getattr__(self, attr: str) -> Any:
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

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Override: listaggregates returns ListElements instead of ListAggregates
        cls.listaggregates = {
            k: v for k, v in cls._superdict.items() if isinstance(v, Types.ListElement)
        }

    def _apply_args(self, *args: object) -> None:
        # Interpret positional args as contained list items (of variable #)
        if len(self.listaggregates) != 1:
            raise ValueError(
                f"{self.__class__.__name__} must have exactly one list aggregate"
            )
        converter = next(iter(self.listaggregates.values()))
        for member in args:
            self.append(converter.convert(member))

    def _listAppend(self, root: ET.Element, member: Any) -> None:
        if len(self.listaggregates) != 1:
            raise ValueError(
                f"{self.__class__.__name__} must have exactly one list aggregate"
            )
        attr, converter = next(iter(self.listaggregates.items()))

        text = converter.unconvert(member)
        ET.SubElement(root, attr.upper()).text = text


# Bootstrap cached attr mappings for the base classes themselves.
# __init_subclass__ handles all subclasses automatically; these two calls
# cover Aggregate and ElementList since they are not their own subclasses.
Aggregate._init_class_attrs()
ElementList._init_class_attrs()
ElementList.listaggregates = {
    k: v for k, v in ElementList._superdict.items() if isinstance(v, Types.ListElement)
}
