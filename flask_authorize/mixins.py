# -*- coding: utf-8 -*-
#
# Database mixins
#
# ------------------------------------------------


# imports
# -------
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr


# types
# -----
import json
from sqlalchemy import TypeDecorator, types

class Permission(TypeDecorator):
    """
    SQLite, MySQL, and PostgreSQL compatible type
    for json column.
    """
    impl = String

    @property
    def python_type(self):
        return object

    def process_bind_param(self, value, dialect):
        # process ambiguous inputs into consistent
        # internal representation
        return json.dumps(value)

    def process_literal_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None


# mixins
# ------
class PermissionsMixin(object):
    """
    Database mixin to use with Flask-Authorize for enabling permissions
    on instances of content models.

    NEED TO INCLUDE MORE DOCS

    """
    __permissions__ = 764

    # foreign keys
    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey('users.id'))

    @declared_attr
    def group_id(cls):
        return Column(Integer, ForeignKey('groups.id'))

    # relationships
    @declared_attr
    def owner(cls):
        return relationship('User', backref=backref(
            'articles', cascade="all, delete-orphan",
        ))

    @declared_attr
    def group(cls):
        return relationship('Group', backref=backref(
            'articles', cascade="all, delete-orphan",
        ))

    # properties
    @declared_attr
    def permissions(cls):
        return Column(Permission, default=cls.__permissions__)
