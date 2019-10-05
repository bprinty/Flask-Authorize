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


# mixins
# ------
class PermissionsMixin(object):
    """
    Database mixin to use with Flask-Authorize for enabling permissions
    on instances of content models.

    NEED TO INCLUDE MORE DOCS

    """
    __permissions__ = '666'

    # base
    @declared_attr
    def permissions(cls):
        return Column(String(3), default=cls.__permissions__)

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
