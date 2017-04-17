# vim: set fileencoding=utf-8
""" Extended SQLAlchemy column types """

# stdlib imports
import decimal
import warnings

# 3rd party imports
import sqlalchemy

# local imports
import ofxtools.Types


class OFXNumeric(sqlalchemy.types.TypeDecorator):
    """
    Handles Euro-style decimal separators (comma) inbound to the DB
    """
    impl = sqlalchemy.types.Numeric

    def process_bind_param(self, value, dialect):
        if value == 0:
            return decimal.Decimal('0')
        elif value:
            # Handle Euro-style decimal separators (comma)
            try:
                value = decimal.Decimal(value)
            except decimal.InvalidOperation:
                if isinstance(value, str):
                    value = decimal.Decimal(value.replace(',', '.'))
                else:
                    raise
            return value


class OFXDateTime(sqlalchemy.types.TypeDecorator):
    """
    Handles datetimes inbound to the DB in formats given by OFX spec
    """
    impl = sqlalchemy.types.DateTime

    def process_bind_param(self, value, dialect):
        return ofxtools.Types.DateTime().convert(value)


class OFXBoolean(sqlalchemy.types.TypeDecorator):
    """
    Handles bools inbound to the DB in format given by OFX spec
    """
    impl = sqlalchemy.types.Boolean
    mapping = {'Y': True, 'N': False}

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return self.mapping[value]


class NagString(sqlalchemy.types.TypeDecorator):
    """
    Text that raises a warning length is exceeded.

    Used to handle OFX data that violates the spec with respect to string length
    on non-critical fields.
    """
    impl = sqlalchemy.types.Text

    def __init__(self, *args, **kwargs):
        """
        Pop the input length, store as self.nagLength, and continue.
        """
        if not hasattr(self.__class__, 'impl'):
            raise AssertionError("TypeDecorator implementations "
                                 "require a class-level variable "
                                 "'impl' which refers to the class of "
                                 "type being decorated")
        args = list(args)
        try:
            length = kwargs.pop('length', None) or args.pop(0)
        except IndexError:
            length = None
        self.length = length

        self.impl = sqlalchemy.sql.type_api.to_instance(
            self.__class__.impl, *args, **kwargs
        )

    def process_bind_param(self, value, dialect):
        if value is None:
            value = ''
        value = str(value)

        if self.length is not None and len(value) > self.length:
            msg = "Value '%s' exceeds length=%s" % (value, self.length)
            warnings.warn(msg, category=ofxtools.Types.OFXTypeWarning) 

        return value
        
