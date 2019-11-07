# -*- coding: utf-8 -*-
#
# Database mixins
#
# ------------------------------------------------


# imports
# -------
import six
import re
import json
from flask import current_app
from werkzeug.exceptions import Unauthorized
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import TypeDecorator, inspect


# types
# -----
class JSON(TypeDecorator):
    """
    SQLite, MySQL, and PostgreSQL compatible type
    for json column.
    """
    impl = String

    @property
    def python_type(self):
        return object

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None


class PipedList(TypeDecorator):
    """
    SQLite, MySQL, and PostgreSQL compatible type
    for column that renders as list when referenced
    in python and a string where list entries are
    separated by pipes '|' when referenced in the
    database.
    """
    impl = String

    @property
    def python_type(self):
        return object

    def process_bind_param(self, value, dialect):
        if not value:
            return None
        return '|'.join(value)

    def process_result_value(self, value, dialect):
        try:
            if not value:
                return []
            return value.split('|')
        except (ValueError, TypeError):
            return None


# helpers
# -------
MODELS = dict()


def gather_models():
    """
    Inspect sqlalchemy models from current context and set global
    dictionary to be used in url conversion.
    """
    global MODELS

    from flask import current_app
    if 'sqlalchemy' not in current_app.extensions:
        return
    check = current_app.config['AUTHORIZE_IGNORE_PROPERTY']

    # inspect current models and add to map
    db = current_app.extensions['sqlalchemy'].db
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and issubclass(cls, db.Model):
            if hasattr(cls, check) and not getattr(cls, check):
                continue
            MODELS[table_key(cls)] = cls
    return


def table_key(cls):
    """
    Parse table key from sqlalchemy class, based on user-specified
    configuration included for extension.
    """
    # class name
    if current_app.config['AUTHORIZE_MODEL_PARSER'] == 'class':
        return cls.__name__

    # lowercase name
    elif current_app.config['AUTHORIZE_MODEL_PARSER'] == 'lower':
        return cls.__name__.lower()

    # snake_case name
    elif current_app.config['AUTHORIZE_MODEL_PARSER'] == 'snake':
        words = re.findall(r'([A-Z][0-9a-z]+)', cls.__name__)
        if len(words) > 1:
            return '_'.join(map(lambda x: x.lower(), words))

    # table name
    elif current_app.config['AUTHORIZE_MODEL_PARSER'] == 'table':
        mapper = inspect(cls)
        return mapper.tables[0].name


def default_permissions_factory(name):
    """
    Factory for returning default permissions based on name.
    """
    def _(cls=None):
        perms = default_permissions(cls)
        return perms.get(name, [])
    return _


def default_permissions(cls=None):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
    if cls is None or cls.__permissions__ is None:
        return current_app.config['AUTHORIZE_DEFAULT_PERMISSIONS']
    elif isinstance(cls._permissions__, int):
        return parse_permission_set(cls.__permissions__)
    elif isinstance(cls.__permissions__, dict):
        return cls.__permissions__


def default_allowances(cls=None):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
    if cls is not None:
        if not isinstance(cls.__allowances__, dict):
            raise AssertionError('Allowances for model {} must be dictionary type!'.format(cls.__name__))

    # if necessary, gather database models to create default
    global MODELS
    if not MODELS:
        gather_models()
    default = {
        key: current_app.config['AUTHORIZE_DEFAULT_ALLOWANCES']
        for key in MODELS
    }

    # overwrite specified allowances
    if cls is not None:
        default.update(cls.__allowances__)
    return default


def default_restrictions(cls=None):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
    if cls is not None:
        if not isinstance(cls.__restrictions__, dict):
            raise AssertionError('Restrictions for model {} must be dictionary type!'.format(cls.__name__))

    # if necessary, gather database models to create default
    global MODELS
    if not MODELS:
        gather_models()
    default = {
        key: current_app.config['AUTHORIZE_DEFAULT_RESTRICTIONS']
        for key in MODELS
    }

    # overwrite specified allowances
    if cls is not None:
        default.update(cls.__restrictions__)
    return default


def permission_list(number):
    """
    Generate permission list from numeric input.
    """
    if isinstance(number, six.string_types) and len(number) == 1:
        number = int(number)
    if not isinstance(number, int):
        return number

    ret = []
    for mask, name in zip([1, 2, 4], ['delete', 'read', 'update']):
        if number & mask:
            ret.append(name)
    return ret


def parse_permission_set(number):
    """
    Parse numeric permissions and return dictionary with
    explicit permission scheme. Note that this method
    does not account for custom content permissions.
    """
    if isinstance(number, six.string_types) and len(number) == 3:
        number = int(number)
    if not isinstance(number, int):
        return number

    # check validity of input
    digits = len(str(number))
    if digits > 3:
        raise AssertionError('Invalid permissions: {}'.format(number))

    # gather permissions
    result = {}
    for digit, check in zip([0, 1, 2], ['other', 'group', 'owner']):
        perm = int(number) // 10 ** digit % 10
        result[check] = permission_list(perm)
    return result


# permissions mixins
# ------------------
class BasePermissionsMixin(object):
    """
    Abstract base class for enabling common functionality
    across various optional permission schemes.
    """
    __permissions__ = None

    @declared_attr
    def other_permissions(cls):
        return Column(PipedList, default=default_permissions_factory('other'))

    @property
    def permissions(self):
        result = {}
        for name in ['owner', 'group', 'other']:
            prop = name + '_permissions'
            if hasattr(self, prop):
                result[name] = getattr(self, prop)
        return result

    @permissions.setter
    def permissions(self, value):
        for name in ['owner', 'group', 'other']:
            if name not in value:
                continue
            prop = name + '_permissions'
            if hasattr(self, prop):
                setattr(self, prop, value[name])
        return

    def set_permissions(self, *args, **kwargs):
        """
        Set permissions explicitly for ACL-enforced content.
        """
        if 'authorize' in current_app.extensions:
            authorize = current_app.extensions['authorize']
            if not authorize.update(self):
                raise Unauthorized

        # handle numeric permission scheme
        if len(args):
            perms = parse_permission_set(args[0])
            kwargs.update(perms)

        # set internal permissions object
        permissions = self.permissions.copy()
        permissions.update(kwargs)
        self.permissions = permissions
        return self


class OwnerMixin(object):
    """
    Mixin providing owner-related database properties
    for object, in the context of enforcing permissions.
    """
    @declared_attr
    def owner_id(cls):
        return Column(Integer, ForeignKey('users.id'))

    @declared_attr
    def owner(cls):
        return relationship('User')

    @declared_attr
    def owner_permissions(cls):
        return Column(PipedList, default=default_permissions_factory('owner'))


class OwnerPermissionsMixin(BasePermissionsMixin, OwnerMixin):
    pass


class GroupMixin(object):
    """
    Mixin providing group-related database properties
    for object, in the context of enforcing permissions.
    """
    @declared_attr
    def group_id(cls):
        return Column(Integer, ForeignKey('groups.id'))

    @declared_attr
    def group(cls):
        return relationship('Group')

    @declared_attr
    def group_permissions(cls):
        return Column(PipedList, default=default_permissions_factory('group'))


class GroupPermissionsMixin(BasePermissionsMixin, GroupMixin):
    pass


# class MultiGroupMixin(object):
#     """
#     Mixin providing groups-related database properties
#     for object, in the context of enforcing permissions.

#     .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES

#     .. note:: NEED TO FIGURE OUT HOW TO AUTOMATICALLY CREATE MAPPING TABLE
#     """
#     @declared_attr
#     def groups(cls):
#         return relationship('Group', backref=backref(
#             'articles', cascade="all, delete-orphan",
#         ))


# class MultiGroupPermissionsMixin(BasePermissionsMixin, MultiGroupMixin):
#     pass


class PermissionsMixin(BasePermissionsMixin, OwnerMixin, GroupMixin):
    """
    Mixin providing owner and group-related database properties
    for object, in the context of enforcing permissions.
    """
    pass


# OwnerGroupPermissionsMixin = PermissionsMixin


# class ComplexPermissionsMixin(BasePermissionsMixin, OwnerMixin, MultiGroupMixin):
#     """
#     Mixin providing owner and multi-group-related database
#     properties for object, in the context of enforcing permissions.

#     .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
#     """
#     pass


# OwnerGroupsPermissionMixin = ComplexPermissionsMixin


# rbac mixins
# -----------
class RestrictionsMixin(object):
    """
    Mixin providing group or role based access control.
    """
    __restrictions__ = dict()

    @declared_attr
    def restrictions(cls):
        return Column(JSON, default=default_restrictions)

    def set_restrictions(self, **kwargs):
        # handle numeric permission scheme
        for key in kwargs:
            kwargs[key] = permission_list(kwargs[key])

        # set internal restrictions object
        restrictions = self.restrictions.copy()
        restrictions.update(kwargs)
        self.restrictions = restrictions
        return self


class AllowancesMixin(object):
    """
    Mixin providing group or role based access control.
    """
    __allowances__ = dict()

    @declared_attr
    def allowances(cls):
        return Column(JSON, default=default_allowances)

    def set_allowances(self, **kwargs):
        # handle numeric permission scheme
        for key in kwargs:
            kwargs[key] = permission_list(kwargs[key])

        # set internal restrictions object
        allowances = self.allowances.copy()
        allowances.update(kwargs)
        self.allowances = allowances
        return self
