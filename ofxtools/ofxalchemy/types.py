# vim: set fileencoding=utf-8
""" Extended SQLAlchemy column types """

# stdlib imports
import decimal

# 3rd party imports
import sqlalchemy

# local imports
import ofxtools.types


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
        return ofxtools.types.DateTime().convert(value)


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
