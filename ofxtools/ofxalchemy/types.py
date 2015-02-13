# vim: set fileencoding=utf-8
""" Extended SQLAlchemy column types """

# stdlib imports
import re
import datetime
import decimal

# 3rd party imports
import sqlalchemy


class Numeric(sqlalchemy.types.TypeDecorator):
    """
    Stores Decimal as String on sqlite, which doesn't have a NUMERIC type
    and by default stores Decimal as float, leading to rounding errors
    """
    impl = sqlalchemy.types.Numeric

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(sqlalchemy.types.CHAR(32))
        else:
            return dialect.type_descriptor(sqlalchemy.types.Numeric)

    def process_bind_param(self, value, dialect):
        if dialect.name == 'sqlite':
            if value:
                return str(value)
            else:
                return ''
        elif value:
            return decimal.Decimal(value)

    def process_result_value(self, value, dialect):
        if value == 0:
            return decimal.Decimal('0')
        elif value:
            return decimal.Decimal(value)


class OFXDateTimeConverter(object):
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

# Custom SQLAlchemy column types
class OFXDateTime(sqlalchemy.types.TypeDecorator):
    """ """
    impl = sqlalchemy.types.DateTime

    def process_bind_param(self, value, dialect):
        return OFXDateTimeConverter.convert(value)

    def process_result_param(self, value, dialect):
        pass


