# -*- coding: utf-8 -*-
#
# Database mixins
#
# ------------------------------------------------


# imports
# -------
import re
import json
from flask import current_app
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

    # inspect current models and add to map
    db = current_app.extensions['sqlalchemy'].db
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and issubclass(cls, db.Model):

            # class name
            if current_app.config['AUTHORIZE_MODEL_PARSER'] == 'default':
                MODELS[cls.__name__] = cls

            # lowercase name
            elif current_app.config['AUTHORIZE_MODEL_PARSER'] == 'lower':
                MODELS[cls.__name__.lower()] = cls

            # snake_case name
            elif current_app.config['AUTHORIZE_MODEL_PARSER'] == 'snake':
                words = re.findall(r'([A-Z][0-9a-z]+)', cls.__name__)
                if len(words) > 1:
                    alias = '_'.join(map(lambda x: x.lower(), words))
                    MODELS[alias] = cls
    return


def default_permissions(cls):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
    if cls.__permissions__ is None:
        return current_app.config['AUTHORIZE_DEFAULT_PERMISSIONS']
    elif isinstance(cls._permissions__, int):
        return parse_permission_set(cls.__permissions__)
    elif isinstance(cls.__permissions__, dict):
        return cls.__permissions__


def default_allowances(cls):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
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
    return default.update(cls.__allowances__)


def default_restrictions(cls):
    """
    Return default permissions for model, falling
    back to app configuration if no default permission
    is explicitly set.
    """
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
    return default.update(cls.__restrictions__)


def permission_list(number):
    """
    Generate permission list from numeric input.
    """
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
            perms = parse_permission_set(args[0])
            permissions.update(perms)

        # set internal permissions object
        self.permissions.update(permissions)
        return


class OwnerMixin(object):
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


class OwnerPermissionsMixin(BasePermissionsMixin, OwnerMixin):
    pass


class GroupMixin(object):
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


class GroupPermissionsMixin(BasePermissionsMixin, GroupMixin):
    pass


class MultiGroupMixin(object):
    """
    Mixin providing groups-related database properties
    for object, in the context of enforcing permissions.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES

    .. note:: NEED TO FIGURE OUT HOW TO AUTOMATICALLY CREATE MAPPING TABLE
    """
    @declared_attr
    def groups(cls):
        return relationship('Group', backref=backref(
            'articles', cascade="all, delete-orphan",
        ))


class MultiGroupPermissionsMixin(BasePermissionsMixin, MultiGroupMixin):
    pass


class PermissionsMixin(BasePermissionsMixin, OwnerMixin, GroupMixin):
    """
    Mixin providing owner and group-related database properties
    for object, in the context of enforcing permissions.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    pass


# rbac mixins
# -----------
class RestrictionsMixin(object):
    """
    Mixin providing group or role based access control.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    __restrictions__ = dict()

    @declared_attr
    def restrictions(cls):
        return Column(Permission, default=default_restrictions)


class AllowancesMixin(object):
    """
    Mixin providing group or role based access control.

    .. note:: NEEDS MORE DOCUMENTATION AND EXAMPLES
    """
    __allowances__ = dict()

    @declared_attr
    def allowances(cls):
        return Column(Permission, default=default_allowances)
