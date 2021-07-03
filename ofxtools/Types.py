"""
Type converters / validators for OFX data content text, used as attributes
of OFX model classes.

Most of the ``ofxtools.Types`` classes correspond to OFX "elements" as defined
in OFX section 1.3.8, i.e. leaf nodes in the SGML/XML hierarcy that bear textual
data content.  These Types implement the data types described in OFX section 3.2.8.

Since the OFX schema is highly nested, some of these class attributes
(e.g. ``SubAggregate``) express parent/child relationships between ``Aggregates``.
"""


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
from functools import singledispatchmethod
import decimal
import datetime
import re
import warnings
from xml.sax import saxutils
from typing import Any, Optional, Union, Type
import inspect


# local imports
from ofxtools import utils


class OFXTypeWarning(UserWarning):
    """Base class for warnings in this module"""


class OFXTypeError(ValueError):
    """Base class for errors in this module"""


class OFXSpecError(OFXTypeError):
    """Violation of the OFX specification"""


def call_signature(*args, **kwargs):
    """Decorator creating ``__signature__`` class attribute (``inspect.Signature`` instance)
    for use by ``__init__()`` method of ``Element`` subclasses.

    Cf. discussion of Parameter/Signature
    pp. 86-101 of David Beazley's "Python 3 Metaprogramming"
    http://dabeaz.com/py3meta/Py3Meta.pdf

    We don't follow Beazley's recommendation to stick the signature construction logic
    in a custom metaclass because we're attracted to the simplicity of reusing Python's
    *arg, **kwarg passing machinery to define the API here.

    N.B. All Elements have ``required`` as keyword-only arg, with a default value of False.
    """
    #  Interpret *args as positional-only args (e.g. SubAggregate.__type__)
    #  that are mandatory (i.e. no default)
    params = [inspect.Parameter(arg, inspect.Parameter.POSITIONAL_ONLY) for arg in args]

    # Interpret **kwargs as args that are optionally positional or keyword e.g. String.length)
    # with the given default value
    params += [
        inspect.Parameter(arg, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default)
        for arg, default in kwargs.items()
    ]

    # All Elements have ``required`` as keyword-only arg, with a default value of False
    params.append(
        inspect.Parameter("required", inspect.Parameter.KEYWORD_ONLY, default=False)
    )

    def decorate(cls):
        cls.__signature__ = inspect.Signature(params)
        return cls

    return decorate


@call_signature()
class Element:
    """Python representation of OFX 'element', i.e. *ML leaf node containing text data.

    Pass validation parameters (e.g. maximum string length, decimal scale,
    required vs. optional, etc.) as arguments to __init__() when defining
    an Aggregate subclass.

    ``Element`` instances are bound to model classes (sundry ``Aggregate``
    subclasses found in the ``ofxtools.models`` subpackage, as well as
    ``OFXHeaderV1``/``OFXHeaverV2`` classes found in the header module).
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

    __type__: Any = NotImplemented  # define in subclass

    def __init__(self, *args, **kwargs):
        """ """
        bound = self.__signature__.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, val in bound.arguments.items():
            setattr(self, name, val)

    def __repr__(self) -> str:
        repr = f"<{self.__class__.__name__}"

        # Mypy doesn't understand that ``__signature__`` gets set by ``__init__()``
        for attr in self.__signature__.parameters:  # type: ignore
            val = getattr(self, attr)
            repr += f" {attr}={val}"

        repr += ">"
        return repr

    #  Descriptor protocol
    def __set_name__(self, owner, name):
        #  Cf. PEP 487
        self.name = name

    def __get__(self, obj, objtype=None):
        """
        ``self`` is the instance of the descriptor
        ``obj`` is the instance of the object your descriptor is attached to.
        ``objtype`` is the type of the object the descriptor is attached to.
        """
        return obj.__dict__[self.name]

    def __set__(self, obj, value) -> None:
        """Perform validation and type conversion before setting value.

        ``self`` is the instance of the descriptor
        ``obj`` is the instance of the object your descriptor is attached to.
        """
        obj.__dict__[self.name] = self.convert(value)

    def convert(self, value):
        """Define in subclass"""
        raise NotImplementedError

    def enforce_required(self, value):
        """Utility used by many subclass converters"""
        if value is None and self.required:
            raise OFXSpecError(f"{self.__class__.__name__}: Value is required")

        return value


class Bool(Element):
    __type__ = bool
    mapping = {"Y": True, "N": False}

    @singledispatchmethod
    def convert(self, value):
        # By default, any type not specifically dispatched raises an error
        msg = f"{value} is not one of the allowed values {self.mapping.keys()}"
        raise OFXSpecError(msg)

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @convert.register
    def _convert_bool(self, value: bool):
        return value

    @convert.register
    def _convert_str(self, value: str) -> bool:
        try:
            return self.mapping[value]
        except KeyError:
            msg = f"{value} is not one of the allowed values {self.mapping.keys()}"
            raise OFXSpecError(msg)

    @singledispatchmethod
    def unconvert(self, value):
        msg = f"{value} is not one of the allowed values {self.mapping.keys()}"
        raise OFXSpecError(msg)

    @unconvert.register
    def _unconvert_bool(self, value: bool) -> str:
        return {v: k for k, v in self.mapping.items()}[value]

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


@call_signature(length=None)
class String(Element):
    __type__ = str
    strict = True

    @singledispatchmethod
    def convert(self, value):
        # By default, any type not specifically dispatched raises an error
        raise TypeError(f"{value!r} is not a str")

    def enforce_length(self, value: str) -> str:
        # Mypy doesn't understand that ``length`` gets set by ``__init__()``
        if self.length is not None and len(value) > self.length:  # type: ignore
            msg = f"{type(self).__name__}: {value!r} exceeds max length={self.length}"  # type: ignore
            if self.strict:
                raise OFXSpecError(msg)
            else:
                warnings.warn(msg, category=OFXTypeWarning)
        return value

    @convert.register
    def _convert_str(self, value: str) -> Optional[str]:
        if value == "":
            return self.enforce_required(None)

        # Unescape '&amp;' '&lt;' '&gt;' '&nbsp;' per OFX section 2.3
        # Also go ahead and unescape other XML control characters,
        # because FIs tend to mix &amp; match...
        value = saxutils.unescape(value, {"&nbsp;": " ", "&apos;": "'", "&quot;": '"'})
        return self.enforce_length(value)

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @singledispatchmethod
    def unconvert(self, value):
        # By default, any type not specifically dispatched raises an error
        raise TypeError(f"{value!r} is not an instance of {self.__class__.__name__}")

    @unconvert.register
    def _unconvert_str(self, value: str):
        return self.enforce_length(value)

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


class NagString(String):
    """String that raises a warning length is exceeded.

    Used to handle OFX data that violates the spec with respect to
    string length on non-critical fields.
    """

    strict = False


class OneOf(Element):
    """Enum data type.

    Usage example from ``OPTINFO``:
    >> opttype = OneOf("CALL", "PUT", required=True)

    N.B. the variable number of positional args used for instantiation violates the
    assumptions of ``call_signature``, so we skip the ``@call_signature`` decorator
    and directly create the ``__signature__`` attribute in the class definition.
    """

    __type__ = str
    __signature__ = inspect.Signature(
        (
            inspect.Parameter("valid", kind=inspect.Parameter.VAR_POSITIONAL),
            inspect.Parameter(
                "required", kind=inspect.Parameter.KEYWORD_ONLY, default=False
            ),
        )
    )

    @singledispatchmethod
    def convert(self, value):
        return self._convert_default(value)

    def _convert_default(self, value):
        value = self.enforce_required(value)
        if value is not None and value not in self.valid:
            raise OFXSpecError(f"'{value}' is not OneOf {self.valid}")
        return value

    @convert.register
    def _convert_str(self, value: str):
        return self._convert_default(value or None)

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @singledispatchmethod
    def unconvert(self, value):
        value = self.enforce_required(value)
        if value is not None and value not in self.valid:
            raise OFXSpecError(f"'{value}' is not OneOf {self.valid}")
        return value

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


@call_signature(length=None)
class Integer(Element):
    __type__ = int

    def enforce_length(self, value: int) -> int:
        # Mypy doesn't understand that ``length`` gets set by ``__init__()``
        length = self.length  # type: ignore
        if length is not None and value >= 10 ** length:
            msg = f"'{value}' has too many digits; max digits={length}"
            raise OFXSpecError(msg)
        return value

    @singledispatchmethod
    def convert(self, value):
        # By default, attempt a naive conversion to subclass type
        return self.enforce_length(int(value))

    @convert.register
    def _convert_int(self, value: int):
        value = self.enforce_length(value)
        return value

    @convert.register
    def convert_str(self, value: str) -> Optional[int]:
        if len(value) == 0:
            return self.enforce_required(None)
        return self.enforce_length(int(value))

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @singledispatchmethod
    def unconvert(self, value):
        # By default, any type not specifically dispatched raises an error
        raise TypeError(f"{value!r} is not an instance of {self.__class__.__name__}")

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @unconvert.register
    def _unconvert_int(self, value: int) -> str:
        value = self.enforce_length(value)
        return str(value)


#  N.B. "scale" here means "decimal places"
#  i.e. Decimal(2).convert("12345.67890") is Decimal("12345.68")
@call_signature(scale=None)
class Decimal(Element):
    __type__ = decimal.Decimal

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #  Rewrite ``self.scale`` from # of digits to a ``decimal.Decimal`` instance
        #  That can be directly fed into ``decimal.Decimal.quantize()``
        if self.scale is not None:
            self.scale = decimal.Decimal(f"0.{'0' * (self.scale - 1)}1")

    @singledispatchmethod
    def convert(self, value):
        """Default dispatch convert() for unregistered type"""
        # None should be dispatched to _convert_none()
        assert value is not None
        # By default, attempt a naive conversion to subclass type
        return self.__type__(value)

    @convert.register
    def _convert_decimal(self, value: decimal.Decimal):
        if self.scale is not None:
            value = value.quantize(self.scale)
        return value

    @convert.register
    def _convert_str(self, value: str) -> decimal.Decimal:
        # Handle Euro-style decimal separators (comma)
        try:
            dec = decimal.Decimal(value)
        except decimal.InvalidOperation:
            dec = decimal.Decimal(value.replace(",", "."))

        if self.scale is not None:
            dec = dec.quantize(self.scale)

        return dec

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @singledispatchmethod
    def unconvert(self, value):
        # By default, any type not specifically dispatched raises an error
        raise TypeError(f"{value!r} is not an instance of {self.__class__.__name__}")

    @unconvert.register
    def _unconvert_decimal(self, value: decimal.Decimal):
        if self.scale is not None and not value.same_quantum(self.scale):
            raise ValueError(f"'{value}' doesn't match scale={self.scale}")
        return str(value)

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


# Valid datetime formats per the OFX spec (in OFX_Common.xsd):
#  [0-9]{4}
#  ((0[1-9])|(1[0-2]))
#  ((0[1-9])|([1-2][0-9])|(3[0-1]))|

#  [0-9]{4}
#  ((0[1-9])|(1[0-2]))
#  ((0[1-9])|([1-2][0-9])|(3[0-1]))
#  (([0-1][0-9])|(2[0-3]))
#  [0-5][0-9]
#  (([0-5][0-9])|(60))|

#  [0-9]{4}
#  ((0[1-9])|(1[0-2]))
#  ((0[1-9])|([1-2][0-9])|(3[0-1]))
#  (([0-1][0-9])|(2[0-3]))
#  [0-5][0-9]
#  (([0-5][0-9])|(60))
#  \.[0-9]{3}|

#  [0-9]{4}
#  ((0[1-9])|(1[0-2]))
#  ((0[1-9])|([1-2][0-9])|(3[0-1]))
#  (([0-1][0-9])|(2[0-3]))
#  [0-5][0-9]
#  (([0-5][0-9])|(60))
#  \.[0-9]{3}
#  (\[[\+\-]?.+(:.+)?\])?
#
# WORKAROUND
# JPM sends DTPOSTED formatted as YYYYMMDDHHMMSS[offset], which isn't
# valid per the spec.  We allow it.
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
    __type__: Union[Type[datetime.datetime], Type[datetime.time]] = datetime.datetime
    regex = DT_REGEX

    @singledispatchmethod
    def convert(self, value):
        cls = value.__class__.__name__
        raise TypeError(f"{value!r} is type '{cls}'; can't convert to {self.__type__}")

    @convert.register
    def _convert_datetime(self, value: datetime.datetime):
        if value.utcoffset() is None:
            raise ValueError(f"{value} is not timezone-aware")
        return value

    @convert.register
    def _convert_str(self, value: str):
        match = self.regex.match(value)
        if match is None:
            msg = f"'{value}' does not conform to OFX formats for {self.__type__}"
            raise OFXSpecError(msg)

        matchdict = match.groupdict()

        gmt_offset = self.parse_gmt_offset(
            matchdict.pop("gmt_offset_hours"),
            matchdict.pop("gmt_offset_minutes"),
            matchdict.pop("tz_name"),
        )

        intmatches = {k: int(v or 0) for k, v in matchdict.items()}

        # OFX time formats give milliseconds,
        # but datetime.datetime wants microseconds
        intmatches["microsecond"] = 1000 * intmatches.pop("millisecond")
        # Mypy doesn't understand passing ``**intmatches`` to instantiate
        return self.normalize_to_gmt(self.__type__(**intmatches), gmt_offset)  # type: ignore

    def parse_gmt_offset(
        self, hours: Optional[str], minutes: Optional[str], tz_name: Optional[str]
    ) -> datetime.timedelta:
        try:
            gmt_offset_hours = int(hours or 0)
        except ValueError:
            # Interactive Brokers sends invalid date/time data formatted like
            #  YYYYMMDDHHMMSS.XXX[-:TZ]
            # If we can't parse hours, try to infer from TZ name
            if tz_name not in utils.TZS:
                msg = f"Can't parse timezone '{tz_name}' into a valid GMT offset"
                raise ValueError(msg)

            gmt_offset_hours = utils.TZS[tz_name]

        return utils.gmt_offset(gmt_offset_hours, int(minutes or 0))

    def normalize_to_gmt(self, value, gmt_offset):
        # Adjust timezone to GMT/UTC
        self.unconvert.register(datetime.datetime, self._unconvert_datetime)
        return (value - gmt_offset).replace(tzinfo=utils.UTC)

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @singledispatchmethod
    def unconvert(self, value):
        # By default, any type not specifically dispatched raises an error
        raise TypeError(f"{value!r} is not an instance of {self.__class__.__name__}")

    @unconvert.register
    def _unconvert_datetime(self, value: datetime.datetime):
        if not hasattr(value, "utcoffset") or value.utcoffset() is None:
            msg = f"'{value}' must be a timezone-aware {self.__type__} instance"
            raise ValueError(msg)

        return format_datetime("%Y%m%d%H%M%S", value)

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


# Valid time formats given by OFX spec (in OFX_Common.xsd):
#  (([0-1][0-9])|(2[0-3]))
#  [0-5][0-9]
#  (([0-5][0-9])|(60))
#  (\.[0-9]{3})?
#  (\[[\+\-]?.+(:.+)?\])?
#
# N.B. the language from section 3.2.8.3 gives the format as:
# HHMMSS.XXX[gmt offset[:tz name]]
# This is inconsistent with the regex from the schema.  We follow the
# schema rather than the human language version
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

    @singledispatchmethod
    def convert(self, value):
        cls = value.__class__.__name__
        raise TypeError(f"{value!r} is type '{cls}'; can't convert to {self.__type__}")

    @convert.register
    def _convert_time(self, value: datetime.time):
        if value.utcoffset() is None:
            raise ValueError(f"{value} is not timezone-aware")
        return value

    def normalize_to_gmt(
        self, value: datetime.time, gmt_offset: datetime.timedelta
    ) -> datetime.time:
        # Adjust timezone to GMT/UTC
        # Can't directly add datetime.time and datetime.timedelta
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

    @convert.register
    def _convert_str(self, value: str):
        return super()._convert_str(value)  # type: ignore

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    @singledispatchmethod
    def unconvert(self, value):
        # By default, any type not specifically dispatched raises an error
        raise TypeError(f"{value!r} is not an instance of {self.__class__.__name__}")

    @unconvert.register
    def _unconvert_time(self, value: datetime.time):
        if not hasattr(value, "utcoffset") or value.utcoffset() is None:
            msg = f"'{value}' must be a timezone-aware {self.__type__} instance"
            raise ValueError(msg)

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

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


@call_signature("converter")
class ListElement(Element):
    """
    ``Element`` that can be repeated on the parent ``Aggregate``.

    Pass the underlying ``Element`` as the first arg to ``__init__()``.
    Constraints may be passed to the underying ``Element`` type, e.g.

        ``ListElement(String(32))``
    """

    def convert(self, value):
        return self.converter.convert(value)

    def unconvert(self, value):
        return self.converter.unconvert(value)


@call_signature("__type__")
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

    @singledispatchmethod
    def convert(self, value):
        if not isinstance(value, self.__type__):
            raise TypeError(f"'{value}' is not an instance of {self.__type__}")
        return value

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    #  This doesn't get used
    #  def __repr__(self):
    #  return f"<{self.__type__.__name__}>"


class ListAggregate(SubAggregate):
    """
    ``SubAggregate`` that can be repeated on the parent ``Aggregate``.
    """

    def unconvert(self, value):
        if not isinstance(value, self.__type__):
            raise TypeError(f"'{value!r}' is not an instance of {self.__type__}")
        return value


class Unsupported:
    """
    Null Aggregate/Element - not implemented (yet)
    """

    def __get__(self, obj, objtype) -> None:
        pass

    def __set__(self, obj, value) -> None:
        pass

    def __repr__(self) -> str:
        return "<Unsupported>"
