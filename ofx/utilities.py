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
    tz_re = re.compile(r'\[[-+.\d]*:\w*\]')
    formats = ('%Y%m%d%H%M%S.%f', '%Y%m%d%H%M%S', '%Y%m%d')

    @classmethod
    def to_python(cls, value):
        # If it's a datetime or None, don't touch it.
        if isinstance(value, datetime.datetime) or value==None:
            return value

        # Pristine copy of input for error reporting
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        match = cls.tz_re.search(value)
        if match:
            tz_delta = match.group().split(':')[0].lstrip('[')
            tz_delta = int(Decimal(tz_delta)*3600) # in seconds
            value = value[:match.start()]
        else:
            tz_delta = 0

        # Try each supported format
        for format in cls.formats:
            try:
                value = datetime.datetime.strptime(value, format)
                error = False
                break
            except ValueError:
                error = True
                continue
        if error:
            raise ValueError("Datetime '%s' does not match OFX formats %s" % (orig_value, str(cls.formats)))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=tz_delta)
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
            #value = time.strftime('%s[0:GMT]' % cls.formats[1], value)
            value = time.strftime(cls.formats[1], value)
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

#accttypeValidator = valid.validators.OneOf(valid.ACCOUNT_TYPES)