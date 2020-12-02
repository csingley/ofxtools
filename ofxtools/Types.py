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
from typing import Any, Optional


# local imports
from ofxtools import utils


class OFXTypeWarning(UserWarning):
    """ Base class for warnings in this module """


class OFXTypeError(ValueError):
    """ Base class for errors in this module """


class OFXSpecError(OFXTypeError):
    """ Violation of the OFX specification """


class Element:
    """
    Python representation of an OFX 'element', i.e. SGML/XML leaf node that
    contains text data.

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

    type_: Any = NotImplemented  # define in subclass

    def __init__(self, *args, **kwargs):
        """To extend in subclass, call super().__init__(*args, **kwargs)
        last, _AFTER_ any subclass-specific initialization.
        """
        self.required = kwargs.pop("required", False)
        if args or kwargs:
            cls = self.__class__.__name__
            raise ValueError(
                f"Unknown args for '{cls}'- args: {args}; kwargs: {kwargs}"
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} required={self.required}>"

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
        """ Define in subclass """
        raise NotImplementedError

    def enforce_required(self, value):
        """Utility used by many subclass converters"""
        if value is None and self.required:
            raise OFXSpecError(f"{self.__class__.__name__}: Value is required")

        return value


class Bool(Element):
    type_ = bool
    mapping = {"Y": True, "N": False}

    @singledispatchmethod
    def convert(self, value):
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


class String(Element):
    type_ = str
    strict = True

    def __init__(self, *args, **kwargs):
        if args:
            self.length = args[0]
        else:
            self.length = None

        super().__init__(*args[1:], **kwargs)

    @singledispatchmethod
    def convert(self, value):
        raise TypeError(f"{value!r} is not a str")

    def enforce_length(self, value: str) -> str:
        if self.length is not None and len(value) > self.length:
            msg = f"{type(self).__name__}: {value!r} exceeds max length={self.length}"
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
    """
    String that raises a warning length is exceeded.

    Used to handle OFX data that violates the spec with respect to
    string length on non-critical fields.
    """

    strict = False


class OneOf(Element):
    type_ = str

    def __init__(self, *args, **kwargs):
        self.valid = set(args)
        super().__init__(**kwargs)

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


class Integer(Element):
    type_ = int

    def __init__(self, *args, **kwargs):
        if args:
            self.length = args[0]
        else:
            self.length = None
        super().__init__(*args[1:], **kwargs)

    def enforce_length(self, value: int) -> int:
        if self.length is not None and value >= 10 ** self.length:
            msg = f"'{value}' has too many digits; max digits={self.length}"
            raise OFXSpecError(msg)
        return value

    @singledispatchmethod
    def convert(self, value):
        value = int(value)
        return self._convert_int(value)

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


class Decimal(Element):
    type_ = decimal.Decimal
    #  N.B. "scale" here means "decimal places"
    #  i.e. Decimal(2).convert("12345.67890") is Decimal("12345.68")
    scale = None

    def __init__(self, *args, **kwargs):
        if args:
            scale = args[0]
            self.scale = decimal.Decimal("0.{}1".format("0" * (scale - 1)))
        super().__init__(*args[1:], **kwargs)

    @singledispatchmethod
    def convert(self, value):
        """ Default dispatch convert() for unregistered type """
        # None should be dispatched to _convert_none()
        assert value is not None
        # By default, attempt a naive conversion to subclass type
        return self.type_(value)

    @convert.register
    def _convert_decimal(self, value: decimal.Decimal):
        if self.scale is not None:
            value = value.quantize(self.scale)
        return value

    @convert.register
    def _convert_str(self, value: str) -> decimal.Decimal:
        # Handle Euro-style decimal separators (comma)
        try:
            value_ = decimal.Decimal(value)
        except decimal.InvalidOperation:
            value_ = decimal.Decimal(value.replace(",", "."))

        if self.scale is not None:
            value_ = value_.quantize(self.scale)

        return value_

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


class DateTime(Element):
    """ OFX Section 3.2.8.2 """

    type_: Any = datetime.datetime
    regex = DT_REGEX

    @singledispatchmethod
    def convert(self, value):
        cls = value.__class__.__name__
        raise TypeError(f"{value!r} is type '{cls}'; can't convert to {self.type_}")

    @convert.register
    def _convert_datetime(self, value: datetime.datetime):
        if value.utcoffset() is None:
            raise ValueError(f"{value} is not timezone-aware")
        return value

    @convert.register
    def _convert_str(self, value: str):
        match = self.regex.match(value)
        if match is None:
            msg = f"'{value}' does not conform to OFX formats for {self.type_}"
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
        return self.normalize_to_gmt(self.type_(**intmatches), gmt_offset)

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
            msg = f"'{value}' isn't a timezone-aware {self.type_} instance; can't convert to GMT"
            raise ValueError(msg)

        # Transform to GMT
        value = value.astimezone(utils.UTC)

        # Round datetime.datetime microseconds to milliseconds per OFX spec.
        # Can't naively format microseconds via strftime() due
        # to need to round to milliseconds.  Instead, manually round
        # microseconds, then insert milliseconds into string format template.
        millisecond = round(value.microsecond / 1000)  # 99500-99999 round to 1000
        second_delta, millisecond = divmod(millisecond, 1000)
        value += datetime.timedelta(
            seconds=second_delta
        )  # Push seconds dial if necessary

        millisec_str = "{0:03d}".format(millisecond)
        fmt = "%Y%m%d%H%M%S.{}[0:GMT]".format(millisec_str)
        return value.strftime(fmt)

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
    """ OFX Section 3.2.8.3 """

    type_ = datetime.time
    regex = TIME_REGEX

    @singledispatchmethod
    def convert(self, value):
        cls = value.__class__.__name__
        raise TypeError(f"{value!r} is type '{cls}'; can't convert to {self.type_}")

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
            msg = f"'{value}' isn't a timezone-aware {self.type_} instance; can't convert to GMT"
            raise ValueError(msg)

        # Transform to GMT
        dt = datetime.datetime(
            1999,
            6,
            8,
            value.hour,
            value.minute,
            value.second,
            microsecond=value.microsecond,
        )
        dt -= value.utcoffset()  # type: ignore
        milliseconds = "{0:03d}".format((dt.microsecond + 500) // 1000)
        fmt = "%H%M%S.{}[0:GMT]".format(milliseconds)
        return dt.strftime(fmt)

    @unconvert.register
    def _unconvert_none(self, value: None) -> None:
        # Pass through None, unless value is required
        return self.enforce_required(value)


class ListElement(Element):
    """
    ``Element`` that can be repeated on the parent ``Aggregate``.

    Pass the underlying ``Element`` as the first arg to ``__init__()``.
    Constraints may be passed to the underying ``Element`` type, e.g.

        ``ListElement(String(32))``
    """

    def __init__(self, *args, **kwargs):
        self.converter = args[0]
        super().__init__(*args[1:], **kwargs)

    def convert(self, value):
        return self.converter.convert(value)

    def unconvert(self, value):
        return self.converter.unconvert(value)


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

    def __init__(self, *args, **kwargs):
        self.type_ = args[0]
        super().__init__(*args[1:], **kwargs)

    @singledispatchmethod
    def convert(self, value):
        if not isinstance(value, self.type_):
            raise TypeError(f"'{value}' is not an instance of {self.type_}")
        return value

    @convert.register
    def _convert_none(self, value: None):
        # Pass through None, unless value is required
        return self.enforce_required(value)

    #  This doesn't get used
    #  def __repr__(self):
    #  return "<{}>".format(self.type_.__name__)


class ListAggregate(SubAggregate):
    """
    ``SubAggregate`` that can be repeated on the parent ``Aggregate``.
    """

    def unconvert(self, value):
        if not isinstance(value, self.type_):
            raise TypeError(f"'{value!r}' is not an instance of {self.type_}")
        return value


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
