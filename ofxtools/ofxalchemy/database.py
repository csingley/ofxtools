# coding: utf-8
"""
SQLAlchemy declarative base for model classes in this package.
"""

# stdlib imports
from contextlib import contextmanager
import sqlite3


# 3rd party imports
from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from sqlalchemy.ext.declarative import (
    as_declarative,
    declared_attr,
    has_inherited_table,
)


Session = scoped_session(sessionmaker(autocommit=False, autoflush=True,))


@contextmanager
def sessionmanager():
    try:
        yield Session
        Session.commit()
    except:
        Session.rollback()
        raise
    finally:
        Session.remove()


def init_db(db_uri, schema=None, **kwargs):
    engine = create_engine(db_uri, **kwargs)
    Base.metadata.schema = schema
    Base.metadata.create_all(bind=engine)
    Session.configure(bind=engine)
    return engine


@as_declarative()
class Base(object):
    """
    Base class representing the main OFX 'aggregates', i.e. SGML parent nodes
    that contain no data.

    These aggregates are grouped into higher-order containers such as lists
    and statements.  Although such higher-order containers are 'aggregates'
    per the OFX specification, they are not persisted by our model; their
    transitory representations are modelled in ofxalchemy.Parser.
    """
    query = Session.query_property()

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self):
        """
        Lists all non-NULL instance attributes.
        """
        return '<%s(%s)>' % (self.__class__.__name__, ', '.join(
            ['%s=%r' % (c.name, str(getattr(self, c.name)))
             for c in self.__class__.__table__.c
             if getattr(self, c.name) is not None]
        ))

    @classmethod
    def primary_keys(cls):
        return [c.name for c in cls.__table__.c if c.primary_key]

    @staticmethod
    def _bindattr(key, attrs):
        """
        Look up the given primary key's value in the given dict of attributes
        """
        k = key
        try:
            v = attrs[k]
        except KeyError:
            # Allow relationship, not just FK id integer
            if k.endswith('_id'):
                k = k[:-3]
                v = attrs[k]
            else:
                raise
        return k, v

    @classmethod
    def _fingerprint(cls, **attrs):
        """ Extract an instance's primary key dict from a dict of attributes """
        try:
            return dict([cls._bindattr(pk, attrs) for pk in cls.primary_keys()])
        except KeyError:
            msg = "%s: Required attributes %s not satisfied by arguments %s" % (
                cls.__name__, cls.primary_keys(), attrs)
            raise ValueError(msg)

    @classmethod
    def lookupByPk(cls, **attrs):
        """ Return a unique instance (or None) with the given primary key"""
        fingerprint = cls._fingerprint(**attrs)
        query = cls.query().filter_by(**fingerprint)
        return query.one_or_none()


# Configure SQLite to support foreign key constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
