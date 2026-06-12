"""
Type converters / validators for OFX data content text, used as attributes
of OFX model classes.

Most of the ``ofxtools.Types`` classes correspond to OFX "elements" as defined
in OFX section 1.3.8, i.e. leaf nodes in the SGML/XML hierarcy that bear textual
data content.  These Types implement the data types described in OFX section 3.2.8.

Since the OFX schema is highly nested, some of these class attributes
(e.g. ``SubAggregate``) express parent/child relationships between ``Aggregates``.
"""

from __future__ import annotations

__all__ = [
    "OFXTypeWarning",
    "OFXTypeError",
    "OFXSpecError",
    "Element",
    "Bool",
    "String",
    "NagString",
    "OneOf",
    "Integer",
    "Decimal",
    "DateTime",
    "Time",
    "ListElement",
    "SubAggregate",
    "ListAggregate",
    "Unsupported",
]


# stdlib imports
import datetime
import decimal
import re
import warnings
from typing import Any
from xml.sax import saxutils

# local imports
from ofxtools import utils


class OFXTypeWarning(UserWarning):
    """Base class for warnings in this module"""


class OFXTypeError(ValueError):
    """Base class for errors in this module"""


class OFXSpecError(OFXTypeError):
    """Violation of the OFX specification"""


class Element:
    """Python representation of OFX 'element', i.e. *ML leaf node containing text data.

    Pass validation parameters (e.g. maximum string length, decimal scale,
    required vs. optional, etc.) as arguments to __init__() when defining
    an Aggregate subclass.

    ``Element`` instances are bound to model classes (sundry ``Aggregate``
    subclasses found in the ``ofxtools.models`` subpackage, as well as
    ``OFXHeaderV1``/``OFXHeaderV2`` classes found in the header module).
    Since these validators are class attributes, they are shared by all instances
    of a model class.  Therefore ``Elements`` are implemented as data descriptors;
    they intercept calls to ``__get__`` and ``__set__``, which get passed as an
    arg the ``Aggregate`` instance whose attribute you're trying to read/write.

    We don't want to store the attribute value inside the ``Element`` instance, keyed by
    the ``Aggregate`` instance, because that will cause the long-persisting ``Element``
    to keep strong references to an ``Aggregate`` instance that may have no other
    remaining references, thus screwing up our garbage collection & eating up memory.

    Instead, we stick the attribute value where it belongs (i.e on the ``Aggregate``
    instance), keyed by the ``Element`` instance (or even better, some proxy therefor).
    We'll need a reference to the ``Element`` instance as long as any instance of the
    ``Aggregate`` class remains alive, but the ``Aggregate`` instances can be garbage
    collected when no longer needed.

    A good introductory discussion to this use of descriptors is here:
    https://realpython.com/python-descriptors/#how-to-use-python-descriptors-properly

    Prior to setting the data value, each ``Element`` performs validation
    (using the arguments passed to ``__init__()``) and type conversion
    (using the logic implemented in ``convert()``).
    """

    def __init__(self, *, required: bool = False) -> None:
        self.required = required

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} required={self.required}>"

    #  Descriptor protocol
    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if obj is None:
            return self
        try:
            return obj.__dict__[self.name]
        except KeyError:
            raise AttributeError(self.name) from None

    def __set__(self, obj: Any, value: Any) -> None:
        if value is None:
            self.enforce_required(value)
            obj.__dict__[self.name] = None
        else:
            obj.__dict__[self.name] = self.convert(value)

    def convert(self, value: Any) -> Any:
        raise NotImplementedError

    def unconvert(self, value: Any) -> Any:
        if value is None:
            self.enforce_required(value)
            return None
        return self._unconvert(value)

    def _unconvert(self, value: Any) -> Any:
        raise NotImplementedError

    def enforce_required(self, value: Any) -> None:
        if value is None and self.required:
            raise OFXSpecError(f"{self.__class__.__name__}: Value is required")


class Bool(Element):
    mapping = {"Y": True, "N": False}
    reverse_mapping = {True: "Y", False: "N"}

    def convert(self, value: Any) -> Any:
        match value:
            case bool():
                return value
            case str():
                try:
                    return self.mapping[value]
                except KeyError:
                    raise OFXSpecError(
                        f"{value} is not one of the allowed values {list(self.mapping)}"
                    )
            case _:
                raise OFXSpecError(
                    f"{value} is not one of the allowed values {list(self.mapping)}"
                )

    def _unconvert(self, value: Any) -> Any:
        match value:
            case bool():
                return self.reverse_mapping[value]
            case _:
                raise OFXSpecError(
                    f"{value} is not one of the allowed values {list(self.mapping)}"
                )


class String(Element):
    strict = True

    def __init__(self, length: int | None = None, *, required: bool = False) -> None:
        super().__init__(required=required)
        self.length = length

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} length={self.length} required={self.required}>"
        )

    def enforce_length(self, value: str) -> str:
        if self.length is not None and len(value) > self.length:
            msg = f"{type(self).__name__}: {value!r} exceeds max length={self.length}"
            if self.strict:
                raise OFXSpecError(msg)
            else:
                warnings.warn(msg, category=OFXTypeWarning)
        return value

    def convert(self, value: Any) -> Any:
        match value:
            case str():
                if value == "":
                    self.enforce_required(None)
                    return None
                # Unescape '&amp;' '&lt;' '&gt;' '&nbsp;' per OFX section 2.3
                # Also go ahead and unescape other XML control characters,
                # because FIs tend to mix &amp; match...
                value = saxutils.unescape(
                    value, {"&nbsp;": " ", "&apos;": "'", "&quot;": '"'}
                )
                return self.enforce_length(value)
            case _:
                raise TypeError(f"{value!r} is not a str")

    def _unconvert(self, value: Any) -> Any:
        match value:
            case str():
                return self.enforce_length(value)
            case _:
                raise TypeError(
                    f"{value!r} is not an instance of {self.__class__.__name__}"
                )


class NagString(String):
    """String that raises a warning when length is exceeded.

    Used to handle OFX data that violates the spec with respect to
    string length on non-critical fields.
    """

    strict = False


class OneOf(Element):
    """Enum data type.

    Usage example from ``OPTINFO``:
    >>> opttype = OneOf("CALL", "PUT", required=True)
    """

    def __init__(self, *valid: Any, required: bool = False) -> None:
        super().__init__(required=required)
        self.valid = valid

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} valid={self.valid} required={self.required}>"
        )

    def _check(self, value: Any) -> Any:
        self.enforce_required(value)
        if value is not None and value not in self.valid:
            raise OFXSpecError(f"'{value}' is not OneOf {self.valid}")
        return value

    def convert(self, value: Any) -> Any:
        match value:
            case str():
                return self._check(value or None)
            case _:
                return self._check(value)

    def _unconvert(self, value: Any) -> Any:
        return self._check(value)


class Integer(Element):
    def __init__(self, length: int | None = None, *, required: bool = False) -> None:
        super().__init__(required=required)
        self.length = length

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} length={self.length} required={self.required}>"
        )

    def enforce_length(self, value: int) -> int:
        if self.length is not None and value >= 10**self.length:
            raise OFXSpecError(
                f"'{value}' has too many digits; max digits={self.length}"
            )
        return value

    def convert(self, value: Any) -> Any:
        match value:
            case int():
                return self.enforce_length(value)
            case str():
                if len(value) == 0:
                    self.enforce_required(None)
                    return None
                return self.enforce_length(int(value))
            case _:
                return self.enforce_length(int(value))

    def _unconvert(self, value: Any) -> Any:
        match value:
            case int():
                return str(self.enforce_length(value))
            case _:
                raise TypeError(
                    f"{value!r} is not an instance of {self.__class__.__name__}"
                )


#  N.B. "scale" here means "decimal places"
#  i.e. Decimal(2).convert("12345.67890") is Decimal("12345.68")
class Decimal(Element):
    __type__ = decimal.Decimal

    def __init__(self, scale: int | None = None, *, required: bool = False) -> None:
        super().__init__(required=required)
        #  Store scale as a decimal.Decimal quantizer rather than an int
        #  so it can be fed directly into decimal.Decimal.quantize()
        if scale is not None:
            self.scale: decimal.Decimal | None = decimal.Decimal(
                f"0.{'0' * (scale - 1)}1"
            )
        else:
            self.scale = None

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} scale={self.scale} required={self.required}>"
        )

    def convert(self, value: Any) -> Any:
        match value:
            case decimal.Decimal():
                if self.scale is not None:
                    value = value.quantize(self.scale)
                return value
            case str():
                # Handle Euro-style decimal separators (comma)
                try:
                    dec = decimal.Decimal(value)
                except decimal.InvalidOperation:
                    dec = decimal.Decimal(value.replace(",", "."))
                if self.scale is not None:
                    dec = dec.quantize(self.scale)
                return dec
            case _:
                return self.__type__(value)

    def _unconvert(self, value: Any) -> Any:
        match value:
            case decimal.Decimal():
                if self.scale is not None and not value.same_quantum(self.scale):
                    raise ValueError(f"'{value}' doesn't match scale={self.scale}")
                return str(value)
            case _:
                raise TypeError(
                    f"{value!r} is not an instance of {self.__class__.__name__}"
                )


# Valid datetime formats per the OFX spec (in OFX_Common.xsd):
#  YYYYMMDD
#  YYYYMMDDHHMMSS
#  YYYYMMDDHHMMSS.XXX
#  YYYYMMDDHHMMSS.XXX[offset[:tz name]]
#
# WORKAROUND: JPM sends DTPOSTED as YYYYMMDDHHMMSS[offset] (no milliseconds).
# We allow seconds to be optional within the time group, and milliseconds
# to be optional within the seconds group.
DT_REGEX = re.compile(
    r"""
    ^
    (?P<year>[0-9]{4})
    (?P<month>(0[1-9])|(1[0-2]))
    (?P<day>(0[1-9])|([1-2][0-9])|(3[0-1]))
    (
        (
            (?P<hour>([0-1][0-9])|(2[0-3]))
            (?P<minute>[0-5][0-9])
            (
                (?P<second>([0-5][0-9])|(60))
                (
                    (\.(?P<millisecond>[0-9]{3}))?
                    (
                        \[(?P<gmt_offset_hours>[0-9-+]+)
                        (
                            (.(?P<gmt_offset_minutes>\d\d))?
                            (:(?P<tz_name>.*))?
                        )?
                        \]
                    )?
                )?
            )?
        )?
    )?
    $
    """,
    re.VERBOSE,
)


def format_datetime(format: str, value: datetime.datetime) -> str:
    """
    Format a `datetime` or `time` according to the OFX specification.

    The value must include timezone information which will be preserved in the OFX
    string.

    The value is rounded to the nearest millisecond since OFX doesn't support
    microsecond resolution.
    """
    utcoffset = value.utcoffset()
    if utcoffset is None:
        raise ValueError(f"{value} is not timezone-aware")

    # Round to nearest millisecond by adding 500 us and truncating.
    # N.B. the value being increased by half a millisecond is
    # carried forward to this function's return value, to ensure that
    # the rounded time has the seconds dial bumped if necessary.
    value_bumped = value + datetime.timedelta(microseconds=500)
    ms = value_bumped.microsecond // 1000

    # OFX takes the UTC offset formatted as +h[.mm].
    offset_mins = utcoffset // datetime.timedelta(minutes=1)
    hours, mins = divmod(abs(offset_mins), 60)
    sign = "-" if offset_mins < 0 else "+"
    tz = f"{sign}{hours:d}"
    if mins != 0:
        tz += f".{mins:02d}"

    # Note that tzname() is permitted to return None.
    tzname = value.tzname()
    if tzname is not None:
        tz += ":" + tzname

    return f"{value_bumped.strftime(format)}.{ms:03d}[{tz}]"


class DateTime(Element):
    """OFX Section 3.2.8.2"""

    # __type__ must be compatible with Time subclass override
    __type__: type[datetime.datetime] | type[datetime.time] = datetime.datetime
    regex = DT_REGEX

    def convert(self, value: Any) -> Any:
        match value:
            case datetime.datetime():
                if value.utcoffset() is None:
                    raise ValueError(f"{value} is not timezone-aware")
                return value
            case str():
                return self._convert_str(value)
            case _:
                raise TypeError(
                    f"{value!r} is type '{type(value).__name__}'; "
                    f"can't convert to {self.__type__}"
                )

    def _convert_str(self, value: str) -> datetime.datetime:
        match = self.regex.match(value)
        if match is None:
            raise OFXSpecError(
                f"'{value}' does not conform to OFX formats for {self.__type__}"
            )

        matchdict = match.groupdict()

        gmt_offset = self._parse_gmt_offset(
            matchdict.pop("gmt_offset_hours"),
            matchdict.pop("gmt_offset_minutes"),
            matchdict.pop("tz_name"),
        )

        intmatches = {k: int(v or 0) for k, v in matchdict.items()}

        # OFX time formats give milliseconds, but datetime.datetime wants microseconds
        intmatches["microsecond"] = 1000 * intmatches.pop("millisecond")
        return self._normalize_to_gmt(self.__type__(**intmatches), gmt_offset)  # type: ignore[arg-type]

    def _parse_gmt_offset(
        self, hours: str | None, minutes: str | None, tz_name: str | None
    ) -> datetime.timedelta:
        try:
            gmt_offset_hours = int(hours or 0)
        except ValueError:
            # Interactive Brokers sends invalid date/time data formatted like
            #  YYYYMMDDHHMMSS.XXX[-:TZ]
            # If we can't parse hours, try to infer from TZ name
            if tz_name not in utils.TZS:
                raise ValueError(
                    f"Can't parse timezone '{tz_name}' into a valid GMT offset"
                )
            gmt_offset_hours = utils.TZS[tz_name]

        return utils.gmt_offset(gmt_offset_hours, int(minutes or 0))

    def _normalize_to_gmt(
        self, value: datetime.datetime, gmt_offset: datetime.timedelta
    ) -> datetime.datetime:
        return (value - gmt_offset).replace(tzinfo=utils.UTC)

    def _unconvert(self, value: Any) -> Any:
        match value:
            case datetime.datetime():
                if value.utcoffset() is None:
                    raise ValueError(
                        f"'{value}' must be a timezone-aware {self.__type__} instance"
                    )
                return format_datetime("%Y%m%d%H%M%S", value)
            case _:
                raise TypeError(
                    f"{value!r} is not an instance of {self.__class__.__name__}"
                )


# Valid time formats given by OFX spec (in OFX_Common.xsd):
#  HHMMSS
#  HHMMSS.XXX
#  HHMMSS.XXX[offset[:tz name]]
#
# N.B. the language from section 3.2.8.3 gives the format as:
# HHMMSS.XXX[gmt offset[:tz name]]
# This is inconsistent with the regex from the schema.  We follow the
# schema rather than the human language version.
TIME_REGEX = re.compile(
    r"""
    ^
    (?P<hour>([0-1][0-9])|(2[0-3]))
    (?P<minute>[0-5][0-9])
    (?P<second>([0-5][0-9])|(60))
    (
        (\.(?P<millisecond>[0-9]{3}))?
        (
            \[(?P<gmt_offset_hours>[0-9-+]+)
            (
                (.(?P<gmt_offset_minutes>\d\d))?
                (:(?P<tz_name>.*))?
            )?
            \]
        )?
    )?
    $
    """,
    re.VERBOSE,
)


class Time(DateTime):
    """OFX Section 3.2.8.3"""

    __type__ = datetime.time
    regex = TIME_REGEX

    def convert(self, value: Any) -> Any:
        match value:
            case datetime.time():
                if value.utcoffset() is None:
                    raise ValueError(f"{value} is not timezone-aware")
                return value
            case str():
                return self._convert_str(value)
            case _:
                raise TypeError(
                    f"{value!r} is type '{type(value).__name__}'; "
                    f"can't convert to {self.__type__}"
                )

    def _normalize_to_gmt(  # type: ignore[override]
        self, value: datetime.time, gmt_offset: datetime.timedelta
    ) -> datetime.time:
        # Can't directly subtract datetime.timedelta from datetime.time
        dt = datetime.datetime(
            1999,
            6,
            8,
            value.hour,
            value.minute,
            value.second,
            microsecond=value.microsecond,
        )
        return (dt - gmt_offset).time().replace(tzinfo=utils.UTC)

    def _unconvert(self, value: Any) -> Any:
        match value:
            case datetime.time():
                if value.utcoffset() is None:
                    raise ValueError(
                        f"'{value}' must be a timezone-aware {self.__type__} instance"
                    )
                dt = datetime.datetime(
                    1999,
                    6,
                    8,
                    value.hour,
                    value.minute,
                    value.second,
                    microsecond=value.microsecond,
                    tzinfo=value.tzinfo,
                )
                return format_datetime("%H%M%S", dt)
            case _:
                raise TypeError(
                    f"{value!r} is not an instance of {self.__class__.__name__}"
                )


class ListElement(Element):
    """
    ``Element`` that can be repeated on the parent ``Aggregate``.

    Pass the underlying ``Element`` as the first arg to ``__init__()``.
    Constraints may be passed to the underying ``Element`` type, e.g.

        ``ListElement(String(32))``
    """

    def __init__(self, converter: Element, *, required: bool = False) -> None:
        super().__init__(required=required)
        self.converter = converter

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} converter={self.converter!r} required={self.required}>"

    def convert(self, value: Any) -> Any:
        if value is None:
            self.enforce_required(value)
            return None
        return self.converter.convert(value)

    def _unconvert(self, value: Any) -> Any:
        return self.converter._unconvert(value)


class SubAggregate(Element):
    """
    Parent/child relationship between ``Aggregates`` - used for child ``Aggregates``
    that can appear at most once within the parent ``Aggregate``.

    ``SubAggregate`` instances appear only in the model class definitions
    (Aggregate subclasses).  Actual model instances replace these ``SubAggregate``
    instances with the ``Aggregate`` instances to which they refer.

    Pass the underlying ``Aggregate`` as the first arg to ``__init__()``,
    followed by any class attribute constraints, e.g.

        ``SubAggregate(BANKACCTFROM, required=True)``
    """

    def __init__(self, aggregate_type: type, *, required: bool = False) -> None:
        super().__init__(required=required)
        self.aggregate_type = aggregate_type

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.aggregate_type.__name__} required={self.required}>"

    def convert(self, value: Any) -> Any:
        if isinstance(value, self.aggregate_type):
            return value
        raise TypeError(f"'{value}' is not an instance of {self.aggregate_type}")


class ListAggregate(SubAggregate):
    """
    ``SubAggregate`` that can be repeated on the parent ``Aggregate``.
    """

    def _unconvert(self, value: Any) -> Any:
        if not isinstance(value, self.aggregate_type):
            raise TypeError(f"'{value!r}' is not an instance of {self.aggregate_type}")
        return value


class Unsupported(Element):
    """
    Null Aggregate/Element - not implemented (yet)
    """

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        return None

    def __set__(self, obj: Any, value: Any) -> None:
        pass

    def convert(self, value: Any) -> Any:
        return None

    def __repr__(self) -> str:
        return "<Unsupported>"
