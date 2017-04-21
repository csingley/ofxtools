# coding: utf-8
""" OFX element type converters / validators """

# stdlib imports
import decimal
import datetime
import time
import re
import warnings
from weakref import WeakKeyDictionary


# Python 2 emulate Py3K str
try:
    str = unicode
except NameError:
    pass


class OFXTypeWarning(UserWarning):
    """ Base class for warnings in this module """
    pass


class Element(object):
    """
    Python representation of an OFX 'element', i.e. SGML leaf node that
    contains text data.

    Pass validation parameters (e.g. maximum string length, decimal precision,
    required vs. optional, etc.) as arguments to __init__() when defining
    an Aggregate subclass.

    Element instances are data descriptors that perform validation (using the
    arguments passed to __init__()) and type conversion (using the logic
    implemented in convert()) prior to setting the instance data value.
    """
    def __init__(self, *args, **kwargs):
        # All instances of an Aggregate subclass share the same Element
        # instance, so we have to have to handle the instance accounting
        # here in the self.data dictionary.
        # We use WeakKeyDictionary to facilitate memory garbage collection.
        self.data = WeakKeyDictionary()
        self.required = kwargs.pop('required', False)
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        """ Override in subclass """
        if args or kwargs:
            raise ValueError("Unknown args for '%s'- args: %r; kwargs: %r"
                             % (self.__class__.__name__, args, kwargs))

    def convert(self, value):
        """ Override in subclass """
        raise NotImplementedError

    def unconvert(self, value):
        """ Override in subclass """
        return str(value)

    def __get__(self, instance, type_):
        return self.data[instance]

    def __set__(self, instance, value):
        """ Perform validation and type conversion before setting value """
        value = self.convert(value)
        self.data[instance] = value

    def __repr__(self):
        repr = "<{} required={}>"
        return repr.format(self.__class__.__name__, self.required)


class Bool(Element):
    mapping = {'Y': True, 'N': False}

    def convert(self, value):
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        # Pass through values already converted to bool
        # (for instantiating from Aggregate.__init__ rather than parsed
        # via Aggregate.from_etree)
        if isinstance(value, bool):
            return value
        try:
            return self.mapping[value]
        except KeyError as e:
            raise ValueError("%s is not one of the allowed values %s" % (
                e.args[0], self.mapping.keys(), ))

    def unconvert(self, value):
        if value is None:
            return None
        if not isinstance(value, bool):
            raise ValueError("%s is not one of the allowed values %s" % (
                value, self.mapping.keys(), ))

        return {v: k for k, v in self.mapping.items()}[value]


class String(Element):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(String, self)._init(*args, **kwargs)

    def convert(self, value):
        if value == '':
            value = None
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        value = str(value)
        if self.length is not None and len(value) > self.length:
            msg = "'%s' is too long; max length=%s" % (value, self.length)
            raise ValueError(msg)
        return value


class NagString(String):
    """
    String that raises a warning length is exceeded.

    Used to handle OFX data that violates the spec with respect to
    string length on non-critical fields.
    """
    def convert(self, value):
        if value == '':
            value = None
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        value = str(value)
        if self.length is not None and len(value) > self.length:
            msg = "Value '%s' exceeds length=%s" % (value, self.length)
            warnings.warn(msg, category=OFXTypeWarning)
        return value


class OneOf(Element):
    def _init(self, *args, **kwargs):
        self.valid = set(args)
        super(OneOf, self)._init(**kwargs)

    def convert(self, value):
        if value == '':
            value = None
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        if value in self.valid:
            return value
        raise ValueError("'%s' is not OneOf %r" % (value, self.valid))


class Integer(Element):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(Integer, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        value = int(value)
        if self.length is not None and value >= 10**self.length:
            msg = '%s has too many digits; max digits=%s'
            raise ValueError(msg % (value, self.length))
        return int(value)


class Decimal(Element):
    def _init(self, *args, **kwargs):
        precision = 2
        if args:
            precision = args[0]
            args = args[1:]
        self.precision = decimal.Decimal('0.' + '0'*(precision-1) + '1')
        super(Decimal, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None

        # Handle Euro-style decimal separators (comma)
        try:
            value = decimal.Decimal(value)
        except decimal.InvalidOperation:
            if isinstance(value, str):
                value = decimal.Decimal(value.replace(',', '.'))

        return value.quantize(self.precision)


class DateTime(Element):
    # Valid datetime formats given by OFX spec in section 3.2.8.2
    tz_re = re.compile(r'\[([-+]?\d{0,2}\.?\d*):?(\w*)\]')
    # strftime formats keyed by the length of the corresponding string
    formats = {
        18: '%Y%m%d%H%M%S.%f', 14: '%Y%m%d%H%M%S',
        12: '%Y%m%d%H%M', 8: '%Y%m%d'
    }

    def convert(self, value):
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            else:
                return None
        # If it's a datetime, don't touch it.
        if isinstance(value, datetime.datetime):
            return value
        # If it's a date, convert it to datetime (using midnight as the time)
        elif isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time())

        # By this point, if it's not a string something's wrong
        if not isinstance(value, str):
            raise ValueError("'%s' is type '%s'; can't convert to datetime" %
                             (value, type(value)))

        # Pristine copy of input for error reporting purposes
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        chunks = self.tz_re.split(value)
        value = chunks.pop(0)
        if chunks:
            gmt_offset, tz_name = chunks[:2]
            # Some FIs *cough* IBKR *cough* write crap for the TZ offset
            # FIXME - don't set gmt_offset to 0; instead parse tz_name and use
            if gmt_offset == '-':
                gmt_offset = '0'
            # hours -> seconds
            gmt_offset = int(decimal.Decimal(gmt_offset)*3600)
        else:
            gmt_offset = 0

        try:
            format = self.formats[len(value)]
        except KeyError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                             (orig_value, self.formats.values()))

        # OFX spec gives fractional seconds as milliseconds; convert to
        # microseconds as required by strptime()
        if len(value) == 18:
            value = value.replace('.', '.000')

        try:
            value = datetime.datetime.strptime(value, format)
        except ValueError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                             (orig_value, self.formats.values()))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=gmt_offset)
        return value

    def unconvert(self, value):
        """
        Input datetime.date or datetime.datetime in local time;
        output str in GMT.
        """
        if not hasattr(value, 'timetuple'):
            msg = "'%s' isn't a datetime; can't convert to GMT" % value
            raise ValueError(msg)

        # Transform to GMT
        gmt_value = time.gmtime(time.mktime(value.timetuple()))
        # timetuples don't have usec precision
        return time.strftime(self.formats[14], gmt_value)
