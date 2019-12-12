# -*- coding: utf-8 -*-
#
# Plugin Setup
#
# ------------------------------------------------


# imports
# -------
import six
import types
from functools import wraps
from flask import current_app
from werkzeug.exceptions import Unauthorized

from .mixins import default_permissions, default_allowances, table_key


# constants
# ---------
AUTHORIZE_CACHE = dict()
CURRENT_USER = None
EXCEPTION = None


# default customizations
# ----------------------
def flask_login_current_user():
    try:
        from flask_login import current_user
        user = current_user
    except ImportError:
        raise AssertionError(
            'Error: Flask-Authorize requires that either '
            'Flask-Login is used or that `user` is '
            'specified to authorization method')
    return user


# plugin
# ------
class Authorize(object):
    """
    Plugin for updating flask functions to handle class-based URL
    routing.
    """

    def __init__(self, app=None, current_user=flask_login_current_user, exception=Unauthorized):
        if app is not None:
            self.init_app(app)

        # set current user function
        if current_user is not None:
            if not callable(current_user):
                raise AssertionError('Error: `current_user` input must be callable.')
            global CURRENT_USER
            CURRENT_USER = current_user

        if exception is not None:
            if not isinstance(exception, type):
                raise AssertionError('Error: `exception` input must be Exception type')
            global EXCEPTION
            EXCEPTION = Unauthorized
        return

    def init_app(self, app):
        # settings
        app.config.setdefault('AUTHORIZE_DEFAULT_PERMISSIONS', dict(
            owner=['delete', 'read', 'update'],
            group=['read', 'update'],
            other=['read']
        ))
        app.config.setdefault('AUTHORIZE_DEFAULT_ACTIONS', ['create', 'delete', 'read', 'update'])
        app.config.setdefault('AUTHORIZE_DEFAULT_RESTRICTIONS', [])
        app.config.setdefault('AUTHORIZE_DEFAULT_ALLOWANCES', app.config['AUTHORIZE_DEFAULT_ACTIONS'])
        app.config.setdefault('AUTHORIZE_MODEL_PARSER', 'table')
        app.config.setdefault('AUTHORIZE_IGNORE_PROPERTY', '__check_access__')
        app.config.setdefault('AUTHORIZE_ALLOW_ANONYMOUS_ACTIONS', False)
        app.config.setdefault('AUTHORIZE_DISABLE_JINJA', False)

        # add to extensions dict for access
        app.extensions['authorize'] = self
        self.app = app

        # add authorize decorator to jinja context
        if not app.config['AUTHORIZE_DISABLE_JINJA']:
            @app.context_processor
            def inject_authorize():
                return dict(authorize=self)
        return

    def __getattr__(self, key):
        return Authorizer(permission=key)

    @property
    def delete(self):
        return Authorizer(permission='delete')

    @property
    def read(self):
        return Authorizer(permission='read')

    @property
    def update(self):
        return Authorizer(permission='update')

    def create(self, *args):
        return Authorizer(create=args)

    def has_role(self, *args):
        return Authorizer(has_role=args)

    def in_group(self, *args):
        return Authorizer(in_group=args)


# helpers
# -------
def has_permission(expected, actual):
    """
    Check if singular set of expected/actual
    permissions are appropriate.
    """
    x = set(expected).intersection(actual)
    return len(x) == len(expected)


def user_has_role(user, roles):
    """
    Check if specified user has one of the specified roles.
    """
    if not hasattr(user, 'roles'):
        return False
    for role in user.roles:
        check = role.name if hasattr(role, 'name') else str(role)
        if check in roles:
            return True
    return False


def user_in_group(user, groups):
    """
    Check if specified user is in one of the specified groups.
    """
    if not hasattr(user, 'groups'):
        return False
    for group in user.groups:
        check = group.name if hasattr(group, 'name') else str(group)
        if check in groups:
            return True
    return False


def user_is_restricted(user, operation, obj):
    if isinstance(obj, six.string_types):
        key = obj
    elif isinstance(obj, type):
        key = table_key(obj)
    else:
        key = table_key(obj.__class__)

    # gather credentials to check
    credentials = []
    if hasattr(user, 'roles'):
        credentials.extend(user.roles)
    if hasattr(user, 'groups'):
        credentials.extend(user.groups)
    if not len(credentials):
        return False

    # check all credentials
    for cred in credentials:
        if hasattr(cred, 'restrictions') and cred.restrictions is not None:
            check = set(cred.restrictions.get(key, []))
            if len(check.intersection(operation)):
                return True
    return False


def user_is_allowed(user, operation, obj):
    if isinstance(obj, six.string_types):
        key = obj
    elif isinstance(obj, type):
        key = table_key(obj)
    else:
        key = table_key(obj.__class__)

    # gather credentials to check
    credentials = []
    if hasattr(user, 'roles'):
        credentials.extend(user.roles)
    if hasattr(user, 'groups'):
        credentials.extend(user.groups)
    if not len(credentials):
        return True

    # gather allowances from credentials
    allowances, default = [], default_allowances()
    for cred in credentials:

        # if not restricting allowances on one
        # of the credentials, it's allowed
        if not hasattr(cred, 'allowances'):
            return True
        if cred.allowances is None:
            return True

        allowances.extend(cred.allowances.get(key, default))

    # check allowances
    check = set(allowances).intersection(operation)
    if len(check) == len(operation):
        return True

    return False


# processor
# ---------
class Authorizer(object):
    """
    Decorator for authorizing the ability of the current
    user to perform actions on various models.

    .. code-block:: python

        @app.route('/users/<id(User):user>', method=['GET'])
        @authorize.read
        def get_user(user):
            return

        @app.route('/users/<id(User):user>', method=['PUT'])
        @authorize.update
        @authorize.has_role('user-updators')
        def update_user(user):
            return

        @app.route('/users/<ident>', method=['PUT'])
        def update_user(ident):
            user = User.get(id=ident)
            if not authorize.update(user) or not authorize.role('test-role'):
                raise Unauthorized
            return


    """

    def __init__(self, permission=None, has_role=None, in_group=None, create=None):
        def _(arg):
            if arg is None:
                arg = []
            if not isinstance(arg, (list, tuple)):
                arg = [arg]
            return list(arg)

        self.permission = _(permission)
        self.has_role = _(has_role)
        self.in_group = _(in_group)
        self.create = _(create)
        return

    def __bool__(self):
        """
        Proxy for doing conditional on functional methods (i.e. create)
        """
        return self.allowed()

    def __call__(self, *cargs, **ckwargs):

        # dispatch on whether or not being used as decorator
        if not len(cargs):
            raise AssertionError('Authorizer needs to be passed function for decoration or objects to authorize.')
        if not isinstance(cargs[0], types.FunctionType):
            return self.allowed(*cargs, user=ckwargs.get('user'))

        # allow for duplicate decorations on functions
        func = cargs[0]
        if func.__name__ not in AUTHORIZE_CACHE:
            AUTHORIZE_CACHE[func.__name__] = self
        else:
            original = AUTHORIZE_CACHE[func.__name__]
            updated = Authorizer(
                permission=original.permission + self.permission,
                has_role=original.has_role + self.has_role,
                in_group=original.in_group + self.in_group,
                create=original.create + self.create
            )
            AUTHORIZE_CACHE[func.__name__] = updated
            del original
            return func

        @wraps(func)
        def inner(*args, **kwargs):

            # gather all items to check authorization for
            check = list(args) + list(kwargs.values())

            # check if authorized
            auth = AUTHORIZE_CACHE[func.__name__]
            if not auth.allowed(*check):
                raise Unauthorized

            return func(*args, **kwargs)

        return inner

    def allowed(self, *args, **kwargs):

        # look to flask-login for current user
        user = kwargs.get('user')
        if user is None:
            user = CURRENT_USER()

        # otherwise, use current user method
        elif isinstance(user, types.FunctionType):
            user = user()

        # don't allow anything for anonymous users
        if user is None:
            return current_app.config['AUTHORIZE_ALLOW_ANONYMOUS_ACTIONS']

        # authorize if user has relevant role
        if len(self.has_role):
            if user_has_role(user, self.has_role):
                return True
            elif not len(self.permission) and not len(self.create):
                return False

        # authorize if user has relevant group
        if len(self.in_group):
            if user_in_group(user, self.in_group):
                return True
            elif not len(self.permission) and not len(self.create):
                return False

        # authorize create privileges based on access
        if len(self.create):
            for model in self.create:
                if user_is_restricted(user, ['create'], model) or \
                   not user_is_allowed(user, ['create'], model):
                    return False

        # return if no additional permission check needed
        if len(self.permission) == 0:
            return True

        # check permissions on individual instances - all objects
        # must have authorization to proceed.
        operation = set(self.permission)
        for arg in args:

            if not isinstance(arg.__class__, six.class_types):
                continue

            # check role restrictions/allowances
            if user_is_restricted(user, operation, arg):
                return False

            if not user_is_allowed(user, operation, arg):
                return False

            # only check permissions for items that have set permissions
            check = current_app.config['AUTHORIZE_IGNORE_PROPERTY']
            if hasattr(arg, check) and not getattr(arg, check):
                continue
            if not hasattr(arg, 'permissions'):
                continue

            # check other permissions
            check = arg.permissions.get('other', [])
            permitted = has_permission(operation, check)

            # check user permissions
            if hasattr(arg, 'owner'):
                if arg.owner == user:
                    check = arg.permissions.get('owner', [])
                    permitted |= has_permission(operation, check)

            # check group permissions
            if hasattr(arg, 'group'):
                if hasattr(user, 'groups'):
                    if arg.group in user.groups:
                        check = arg.permissions.get('group', [])
                        permitted |= has_permission(operation, check)

            if not permitted:
                return False

        return True
