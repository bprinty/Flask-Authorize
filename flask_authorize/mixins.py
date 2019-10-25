# -*- coding: utf-8 -*-
#
# Database mixins
#
# ------------------------------------------------


# imports
# -------
from flask import current_app
import json
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import TypeDecorator


# types
# -----
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


# helpers
# -------
def default_permissions(cls):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
    if cls.__permissions__ is None:
        return current_app.config['AUTHORIZE_DEFAULT_PERMISSIONS']
    elif isinstance(cls._permissions__, int):
        return parse_numeric_permissions(cls.__permissions__)
    elif isinstance(cls.__permissions__, dict):
        return cls.__permissions__


# def number_to_permission_list():
#     for mask, name in zip([1, 2, 4], ['delete', 'read', 'delete']):
#         perm = int(number) // 10 ** digit % 10
#         if perm & mask:
#             STOPPED HERE
#     return

def parse_numeric_permissions(number):
    """
    Parse numeric permissions and return dictionary with
    explicit permission scheme. Note that this method
    does not account for custom content permissions.
    """
    # check validity of input
    digits = len(str(number))
    if digits > 3:
        raise AssertionError('Invalid permissions: {}'.format(number))

    # gather permissions
    permissions = dict(
        owner=[],
        group=[],
        other=[]
    )
    for digit, check in zip([0, 1, 2], ['other', 'group', 'owner']):
        for mask, name in zip([1, 2, 4], ['delete', 'read', 'delete']):
            perm = int(number) // 10 ** digit % 10
            if perm & mask:
                permissions[check].append(name)
    return permissions


# permissions mixins
# ------------------
class BasePermissionsMixin(object):
    """
    Abstract base class for enabling common functionality
    across various optional permission schemes.
    """
    __permissions__ = None
    
    # properties
    @declared_attr
    def permissions(cls):
        return Column(Permission, default=cls.__permissions__)

    def set_permissions(self, *args, **permissions):
        """
        Set permissions explicitly for ACL-enforced content.
        """
        # handle numeric permission scheme
        if len(args):
            perms = parse_numeric_permissions(args[0])
            permissions.update(perms)

        # set internal permissions object
        self.permissions.update(permissions)
        return


class OwnerMixin(BasePermissionsMixin):
    """
    Mixin providing owner-related database properties
    for object, in the context of enforcing permissions.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey('users.id'))

    @declared_attr
    def owner(cls):
        return relationship('User', backref=backref(
            'articles', cascade="all, delete-orphan",
        ))


class GroupMixin(BasePermissionsMixin):
    """
    Mixin providing group-related database properties
    for object, in the context of enforcing permissions.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    @declared_attr
    def group_id(cls):
        return Column(Integer, ForeignKey('groups.id'))

    @declared_attr
    def group(cls):
        return relationship('Group', backref=backref(
            'articles', cascade="all, delete-orphan",
        ))


class MultiGroupMixin(BasePermissionsMixin):
    """
    Mixin providing groups-related database properties
    for object, in the context of enforcing permissions.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    @declared_attr
    def groups(cls):
        return relationship('Group', backref=backref(
            'articles', cascade="all, delete-orphan",
        ))


class PermissionsMixin(OwnerMixin, GroupMixin):
    """
    Mixin providing owner and group-related database properties
    for object, in the context of enforcing permissions.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    pass


# restrictions mixins
# -------------------
class BaseRestrictionsMixin(object):
    """
    Abstract base class for enabling common functionality
    across various optional permission schemes.
    """
    __restrictions__ = None
    
    # properties
    @declared_attr
    def restrictions(cls):
        return Column(Permission, default=cls.__permissions__)

    def set_restrictions(self, *args, **permissions):
        """
        Set permissions explicitly for ACL-enforced content.
        """
        # handle numeric permission scheme
        if len(args):
            for key
            perms = parse_numeric_permissions(args[0])
            permissions.update(perms)

        # set internal permissions object
        self.permissions.update(permissions)
        return