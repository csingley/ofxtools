import os.path
import re
import datetime
import time

def _(path):
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path

# Validators/converters implemented here so that
# client.py needn't depend on FormEncode
class OFXDtConverter(object):
    # Valid datetime formats given by OFX 3.2.8.2
    tz_re = re.compile(r'\[([-+]?\d{1,2}\.?\d*):?(\w*)\]')
    # strftime formats keyed by the length of the corresponding string
    formats = {18: '%Y%m%d%H%M%S.%f', 14: '%Y%m%d%H%M%S', 8: '%Y%m%d'}

    @classmethod
    def to_python(cls, value):
        # If it's a datetime or None, don't touch it.
        if isinstance(value, datetime.datetime) or value==None:
            return value

        # Pristine copy of input for error reporting
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        chunks = cls.tz_re.split(value)
        value = chunks.pop(0)
        if chunks:
            gmt_offset, tz_name = chunks[:2]
            gmt_offset = int(Decimal(gmt_offset)*3600) # hours -> seconds
        else:
            gmt_offset = 0

        format = cls.formats[len(value)]
        try:
            value = datetime.datetime.strptime(value, format)
        except ValueError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                            (orig_value, str(cls.formats.values())))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=gmt_offset)
        return value

    @classmethod
    def from_python(cls, value):
        """ Input datetime.datetime in local time; output str in GMT. """
        # Pristine copy of input for error reporting
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

class OFXStringBool(object):
    values = {True: 'Y', False: 'N'}

    @classmethod
    def from_python(cls, value):
        return cls.values[value]

class BankAcctTypeValidator(object):
    values = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')

    @classmethod
    def to_python(cls, value):
        assert value in cls.values
        return value
