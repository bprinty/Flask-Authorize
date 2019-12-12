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
from sqlalchemy.orm import relationship
from sqlalchemy.sql import operators
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import TypeDecorator, inspect, and_, or_


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

    def coerce_compared_value(self, op, value):
        if op in (operators.like_op,
                  operators.notlike_op,
                  operators.contains_op):
            return String()
        else:
            return self

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
    # if necessary, gather database models to create default
    global MODELS
    if not MODELS:
        gather_models()

    # configure defaults
    default = {
        key: current_app.config['AUTHORIZE_DEFAULT_ALLOWANCES']
        for key in MODELS
    }

    # if called directly, return the defaults
    if cls is None:
        return default

    # if allowances are explicitly set to something else, use them
    if isinstance(cls.__allowances__, dict):
        return cls.__allowances__

    # otherwise, use defaults
    return default


def default_restrictions(cls=None):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
    # if necessary, gather database models to create default
    global MODELS
    if not MODELS:
        gather_models()

    # configure defaults
    default = {
        key: current_app.config['AUTHORIZE_DEFAULT_RESTRICTIONS']
        for key in MODELS
    }

    # if called directly, return the defaults
    if cls is None:
        return default

    # if set to fail safe, use that
    if cls.__restrictions__ == '*' or cls.__restrictions__ is True:
        return {
            key: current_app.config['AUTHORIZE_DEFAULT_ACTIONS']
            for key in MODELS
        }

    # overwrite specified allowances
    if isinstance(cls.__restrictions__, dict):
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

    @classmethod
    def authorized(cls, check):
        """
        Query operator for permissions mixins. This operator
        can be used in SQLAlchemy query statements, and will
        automatically decorate queries with appropriate owner/group
        and permissionc checks.

        Arguments:
            check (str): Permission to authorize (i.e. read, update)

        Examples:

            Query all articles where the current user is read-authorized:

            .. code-block:: python

                Article.query.filter(Article.authorized('read')).all()


            Query by multiple parameters, including authorization:

            .. code-block:: python

                Article.query.filter(or_(
                    Article.name.contains('open article'),
                    Article.authorized('read')
                ))
        """
        from .plugin import CURRENT_USER
        current_user = CURRENT_USER()
        clauses = [
            cls.other_permissions.contains(check),
        ]
        if hasattr(current_user, 'id'):
            if hasattr(cls, 'owner_id'):
                clauses.append(and_(
                    current_user.id == cls.owner_id,
                    cls.owner_permissions.contains(check)
                ))
            if hasattr(cls, 'group_id') and hasattr(current_user, 'groups'):
                clauses.append(and_(
                    cls.group_id.in_([x.id for x in current_user.groups]),
                    cls.group_permissions.contains(check)
                ))
        return or_(*clauses)

    @property
    def permissions(self):
        """
        Proxy for interacting with permissions dictionary.
        """
        result = {}
        for name in ['owner', 'group', 'other']:
            prop = name + '_permissions'
            if hasattr(self, prop):
                result[name] = getattr(self, prop)
        return result

    @permissions.setter
    def permissions(self, value):
        """
        Setter for permissions dictionary proxy.
        """
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
    __allowances__ = '*'

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
