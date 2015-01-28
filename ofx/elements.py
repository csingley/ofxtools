# vim: set fileencoding=utf-8
""" OFX element type converters / validators """

# stdlib imports
from weakref import WeakKeyDictionary
import decimal
import datetime
import time
import re


class Element(object):
    """
    Python representation of an OFX 'element', i.e. SGML leaf node that contains
    text data.

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
        # here in the self.data dictionary.  We use WeakKeyDictionary
        # to facilitate memory garbage collection.
        self.data = WeakKeyDictionary()
        self.required = kwargs.pop('required', False)
        self.strict = kwargs.pop('strict', True)
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        """ Override in subclass """
        if args or kwargs:
            raise ValueError("Unknown args for '%s'- args: %r; kwargs: %r"
                            % (self.__class__.__name__, args, kwargs))

    def convert(self, value, strict=True):
        """ Override in subclass """
        raise NotImplementedError

    def __get__(self, instance, type_):
        return self.data[instance]

    def __set__(self, instance, value):
        """ Perform validation and type conversion before setting value """
        value = self.convert(value, strict=self.strict)
        self.data[instance] = value


class Bool(Element):
    mapping = {'Y': True, 'N': False}

    def convert(self, value, strict=True):
        if value is None and not self.required:
            return None
        return self.mapping[value]

    def unconvert(self, value):
        if value is None and not self.required:
            return None
        return {v:k for k,v in self.mapping.items()}[value]


class String(Element):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(String, self)._init(*args, **kwargs)

    def convert(self, value, strict=True):
        if value is None and not self.required:
            return None
        if strict and self.length is not None and len(value) > self.length:
            raise ValueError("'%s' is too long; max length=%s" % (value, self.length))
        return str(value)


class OneOf(Element):
    def _init(self, *args, **kwargs):
        self.valid = set(args)
        super(OneOf, self)._init(**kwargs)

    def convert(self, value, strict=True):
        if value is None and not self.required:
            return None
        if (value in self.valid):
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

    def convert(self, value, strict=True):
        if value is None and not self.required:
            return None
        value = int(value)
        if self.length is not None and value >= 10**self.length:
            raise ValueError('%s has too many digits; max digits=%s' % (value, self.length))
        return int(value)


class Decimal(Element):
    def _init(self, *args, **kwargs):
        precision = 2
        if args:
            precision = args[0]
            args = args[1:]
        self.precision = precision
        super(Decimal, self)._init(*args, **kwargs)

    def convert(self, value, strict=True):
        if value is None and not self.required:
            return None
        value = decimal.Decimal(value)
        precision = decimal.Decimal('0.' + '0'*(self.precision-1) + '1')
        value.quantize(precision)
        return value


class DateTime(Element):
    # Valid datetime formats given by OFX spec in section 3.2.8.2
    tz_re = re.compile(r'\[([-+]?\d{0,2}\.?\d*):?(\w*)\]')
    # strftime formats keyed by the length of the corresponding string
    formats = {18: '%Y%m%d%H%M%S.%f', 14: '%Y%m%d%H%M%S', 8: '%Y%m%d'}

    @classmethod
    def convert(cls, value, strict=True):
        # If it's a datetime or None, don't touch it.
        if isinstance(value, datetime.datetime) or value is None:
            return value

        # Pristine copy of input for error reporting purposes
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        chunks = cls.tz_re.split(value)
        value = chunks.pop(0)
        if chunks:
            gmt_offset, tz_name = chunks[:2]
            # Some FIs *cough* IBKR *cough* write crap for the TZ offset
            if gmt_offset == '-':
                gmt_offset = '0'
            gmt_offset = int(decimal.Decimal(gmt_offset)*3600) # hours -> seconds
        else:
            gmt_offset = 0
        format = cls.formats[len(value)]
        try:
            value = datetime.datetime.strptime(value, format)
        except ValueError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                            (orig_value, cls.formats.values()))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=gmt_offset)
        return value

    @classmethod
    def unconvert(cls, value):
        """ Input datetime.datetime in local time; output str in GMT. """
        # Pristine copy of input for error reporting purposes
        orig_value = value

        try:
            # Transform to GMT
            value = time.gmtime(time.mktime(value.timetuple()))
            # timetuples don't have usec precision
            #value = time.strftime('%s[0:GMT]' % cls.formats[14], value)
            value = time.strftime(cls.formats[14], value)
        except:
            raise # FIXME
        return value

