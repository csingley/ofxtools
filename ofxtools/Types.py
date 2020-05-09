# coding: utf-8
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
import functools
import decimal
import datetime
import re
import warnings
from collections import defaultdict
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
    they intercept calls to ``__get__`` and ``__set__`` redirecting them to a
    ``defaultdict`` keyed by the calling parent, where values are the data passed
    to that ``Element``).

    Prior to setting the data value, each ``Element`` performs validation
    (using the arguments passed to ``__init__()``) and type conversion
    (using the logic implemented in ``_convert()``).
    """

    type = NotImplemented  # define in subclass

    def __init__(self, *args, **kwargs):
        self.data = defaultdict(None)
        self.required = kwargs.pop("required", False)

        # N.B. ``functools.singledispatch()`` dispatches on the type of the
        # first argument of a function, so we can't use decorator syntax on
        # a method (unless it's a staticmethod).  Instead we use it in
        # functional form on a bound method.
        self.convert = functools.singledispatch(self._convert)
        self.convert.register(type(None), self._convert_none)
        self.convert.register(str, self._convert_str)

        self.unconvert = functools.singledispatch(self._unconvert)
        self.unconvert.register(type(None), self._unconvert_none)

        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        """ Extend in subclass """
        if args or kwargs:
            cls = self.__class__.__name__
            raise ValueError(
                f"Unknown args for '{cls}'- args: {args}; kwargs: {kwargs}"
            )

    def __get__(self, parent, parent_type):
        # HACK - `parent is not None` is needed for tests/test_models_base.py,
        # else it crashes.
        # Research!
        if parent is not None:
            return self.data[parent]

    def __set__(self, parent, value) -> None:
        """ Perform validation and type conversion before setting value """
        self.data[parent] = self.convert(value)

    def enforce_required(self, value):
        if value is None and self.required:
            raise OFXSpecError(f"{self.__class__.__name__}: Value is required")

        return value

    def _convert(self, value):
        """ Convert OFX to Python data type """
        return self._convert_default(value)

    def _convert_default(self, value):
        """ Default dispatch convert() for unregistered type """
        # None should be dispatched to _convert_none()
        assert value is not None
        # By default, attempt a naive conversion to subclass type
        return self.type(value)

    def _convert_none(self, value):
        """ Dispatch convert() for type(None) """
        # Pass through None, unless value is required
        return self.enforce_required(value)

    def _convert_str(self, value):
        """ Dispatch convert() for str """
        # Interpret empty string as None
        if value == "":
            value = None
            return self._convert_none(value)
        return self._convert_default(value)

    def _unconvert(self, value):
        """ Convert Python data type to OFX """
        return self._unconvert_default(value)

    def _unconvert_default(self, value):
        # By default, any type not specifically dispatched raises an error
        cls = self.__class__.__name__
        raise TypeError(f"{value!r} is not an instance of {cls}")

    def _unconvert_none(self, value: None) -> None:
        """ Dispatch unconvert() for type(None) """
        # Pass through None, unless value is required
        return self.enforce_required(value)

    def __repr__(self) -> str:
        repr = "<{} required={}>"
        return repr.format(self.__class__.__name__, self.required)


class Bool(Element):
    type = bool
    mapping = {"Y": True, "N": False}

    def _init(self, *args, **kwargs):
        self.convert.register(bool, self._convert_bool)
        self.unconvert.register(bool, self._unconvert_bool)
        super()._init(*args, **kwargs)

    def _convert_default(self, value):
        # Better error message than superclass default
        msg = f"{value} is not one of the allowed values {self.mapping.keys()}"
        raise OFXSpecError(msg)

    def _convert_bool(self, value):
        return value

    def _convert_str(self, value):
        try:
            value = self.mapping[value]
        except KeyError:
            msg = f"{value} is not one of the allowed values {self.mapping.keys()}"
            raise OFXSpecError(msg)
        return value

    def _unconvert_default(self, value):
        # Better error message than superclass default
        msg = f"{value} is not one of the allowed values {self.mapping.keys()}"
        raise OFXSpecError(msg)

    def _unconvert_bool(self, value):
        value = {v: k for k, v in self.mapping.items()}[value]
        return value


class String(Element):
    type = str
    strict = True

    def _init(self, *args, **kwargs):
        self.unconvert.register(str, self._unconvert_str)

        length = None
        if args:
            length = args[0]
        self.length = length
        super()._init(*args[1:], **kwargs)

    def _convert_default(self, value):
        # Better error message than superclass default
        raise TypeError(f"'{value!r}' is not a str")

    def enforce_length(self, value: str) -> str:
        if self.length is not None and len(value) > self.length:
            msg = f"Value '{value}' exceeds max length={self.length}"
            if self.strict:
                raise OFXSpecError(msg)
            else:
                warnings.warn(msg, category=OFXTypeWarning)
        return value

    def _convert_str(self, value):
        if value == "":
            value = None
            return self.enforce_required(value)

        # Unescape '&amp;' '&lt;' '&gt;' '&nbsp;' per OFX section 2.3
        # Also go ahead and unescape other XML control characters,
        # because FIs tend to mix &amp; match...
        value = saxutils.unescape(value, {"&nbsp;": " ", "&apos;": "'", "&quot;": '"'})
        return self.enforce_length(value)

    def _unconvert_str(self, value):
        return self.enforce_length(value)


class NagString(String):
    """
    String that raises a warning length is exceeded.

    Used to handle OFX data that violates the spec with respect to
    string length on non-critical fields.
    """

    strict = False


class OneOf(Element):
    type = str

    def _init(self, *args, **kwargs):
        self.valid = set(args)
        super()._init(**kwargs)

    def _convert_default(self, value):
        value = self.enforce_required(value)
        if value is not None and value not in self.valid:
            raise OFXSpecError(f"'{value}' is not OneOf {self.valid}")
        return value

    def _convert_str(self, value):
        if value == "":
            value = None
        return self._convert_default(value)

    def _unconvert_default(self, value):
        value = self.enforce_required(value)
        if value is not None and value not in self.valid:
            raise OFXSpecError(f"'{value}' is not OneOf {self.valid}")
        return value


class Integer(Element):
    type = int

    def _init(self, *args, **kwargs):
        self.convert.register(int, self._convert_int)
        self.unconvert.register(int, self._unconvert_int)

        length = None
        if args:
            length = args[0]
        self.length = length

        super()._init(*args[1:], **kwargs)

    def enforce_length(self, value: int) -> int:
        if self.length is not None and value >= 10 ** self.length:
            msg = f"'{value}' has too many digits; max digits={self.length}"
            raise OFXSpecError(msg)
        return value

    def _convert_default(self, value):
        value = int(value)
        return self._convert_int(value)

    def _convert_int(self, value):
        value = self.enforce_length(value)
        return value

    def _unconvert_int(self, value):
        value = self.enforce_length(value)
        value = str(value)
        return value


class Decimal(Element):
    type = decimal.Decimal
    #  N.B. "scale" here means "decimal places"
    #  i.e. Decimal(2).convert("12345.67890") is Decimal("12345.68")
    scale = None

    def _init(self, *args, **kwargs):
        self.convert.register(decimal.Decimal, self._convert_decimal)
        self.unconvert.register(decimal.Decimal, self._unconvert_decimal)

        if args:
            scale = args[0]
            self.scale = decimal.Decimal("0.{}1".format("0" * (scale - 1)))
        super()._init(*args[1:], **kwargs)

    def _convert_decimal(self, value):
        if self.scale is not None:
            value = value.quantize(self.scale)
        return value

    def _convert_str(self, value):
        # Handle Euro-style decimal separators (comma)
        try:
            value = decimal.Decimal(value)
        except decimal.InvalidOperation:
            value = decimal.Decimal(value.replace(",", "."))

        if self.scale is not None:
            value = value.quantize(self.scale)

        return value

    def _unconvert_decimal(self, value):
        if self.scale is not None and not value.same_quantum(self.scale):
            raise ValueError(f"'{value}' doesn't match scale={self.scale}")
        return str(value)


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

    type: Any = datetime.datetime
    regex = DT_REGEX

    def _init(self, *args, **kwargs):
        self.convert.register(datetime.datetime, self._convert_datetime)
        self.unconvert.register(datetime.datetime, self._unconvert_datetime)
        super()._init(*args, **kwargs)

    def _convert_default(self, value):
        cls = value.__class__.__name__
        raise TypeError(f"{value!r} is type '{cls}'; can't convert to {self.type}")

    def _convert_datetime(self, value):
        if value.utcoffset() is None:
            raise ValueError(f"{value} is not timezone-aware")
        return value

    def _convert_str(self, value):
        match = self.regex.match(value)
        if match is None:
            msg = f"'{value}' does not conform to OFX formats for {self.type}"
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
        return self.normalize_to_gmt(self.type(**intmatches), gmt_offset)

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

    def _unconvert_datetime(self, value):
        if not hasattr(value, "utcoffset") or value.utcoffset() is None:
            msg = f"'{value}' isn't a timezone-aware {self.type} instance; can't convert to GMT"
            raise ValueError(msg)

        # Transform to GMT
        value = value.astimezone(utils.UTC)

        # Round datetime.datetime microseconds to milliseconds per OFX spec.
        # Can't naively format microseconds via strftime() due
        # to need to round to milliseconds.  Instead, manually round
        # microseconds, then insert milliseconds into string format template.
        millisecond = (value.microsecond + 500) // 1000

        # Round up microseconds above 999499; increment seconds (Issue #80)
        if millisecond > 999:
            assert millisecond == 1000
            millisecond = 0
            value = value + datetime.timedelta(seconds=1)

        milliseconds = "{0:03d}".format(millisecond)
        fmt = "%Y%m%d%H%M%S.{}[0:GMT]".format(milliseconds)
        return value.strftime(fmt)


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

    type = datetime.time
    regex = TIME_REGEX

    def _init(self, *args, **kwargs):
        self.convert.register(datetime.time, self._convert_time)
        self.unconvert.register(datetime.time, self._unconvert_time)

        super()._init(*args, **kwargs)

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

    def _convert_time(self, value):
        if value.utcoffset() is None:
            raise ValueError(f"{value} is not timezone-aware")
        return value

    def _convert_datetime(self, value):
        return self._convert_default(value)

    def _unconvert_time(self, value):
        if not hasattr(value, "utcoffset") or value.utcoffset() is None:
            msg = f"'{value}' isn't a timezone-aware {self.type} instance; can't convert to GMT"
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
        dt -= value.utcoffset()
        milliseconds = "{0:03d}".format((dt.microsecond + 500) // 1000)
        fmt = "%H%M%S.{}[0:GMT]".format(milliseconds)
        return dt.strftime(fmt)

    def _unconvert_datetime(self, value):
        return self._unconvert_default(value)


class ListElement(Element):
    """
    ``Element`` that can be repeated on the parent ``Aggregate``.

    Pass the underlying ``Element`` as the first arg to ``__init__()``.
    Constraints may be passed to the underying ``Element`` type, e.g.

        ``ListElement(String(32))``
    """

    def _init(self, *args, **kwargs):
        self.converter = args[0]
        super()._init(*args[1:], **kwargs)

    def _convert_default(self, value):
        return self.converter.convert(value)

    def _unconvert_default(self, value):
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

    def _init(self, *args, **kwargs):
        self.type = args[0]
        super()._init(*args[1:], **kwargs)

    def _convert_default(self, value):
        if not isinstance(value, self.type):
            raise TypeError(f"'{value}' is not an instance of {self.type}")
        return value

    #  This doesn't get used
    #  def __repr__(self):
    #  return "<{}>".format(self.type.__name__)


class ListAggregate(SubAggregate):
    """
    ``SubAggregate`` that can be repeated on the parent ``Aggregate``.
    """

    def _unconvert_default(self, value):
        if not isinstance(value, self.type):
            raise TypeError(f"'{value!r}' is not an instance of {self.type}")
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
