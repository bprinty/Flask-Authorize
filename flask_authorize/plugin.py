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

# constants
# ---------
AUTHORIZE_CACHE = dict()
CURRENT_USER = None


# helpers
# -------
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

    def __init__(self, app=None, current_user=flask_login_current_user):
        if app is not None:
            self.init_app(app, current_user=current_user)

        return

    def init_app(self, app, current_user=None):
        # settings
        app.config.setdefault('AUTHORIZE_DEFAULT_PERMISSIONS', dict(
            owner=['read', 'update', 'delete'],
            group=['read', 'update'],
            other=['read']
        ))

        self.app = app

        # set current user function
        if current_user is not None:
            if not callable(current_user):
                raise AssertionError('Error: `current_user` input must be callable.')
            global CURRENT_USER
            CURRENT_USER = current_user
        return

    @property
    def read(self):
        return Authorizer(permit=2)

    @property
    def write(self):
        return Authorizer(permit=4)

    @property
    def role(roles, user=None):
        return Authorizer(roles=roles, permit='rw')

    @property
    def roles(roles, user=None):
        return Authorizer(roles=roles, permit='rw')


# worker
# ------
class Authorizer(object):
    """
    Decorator for authorizing the ability of the current
    user to perform actions on various models.

    .. code-block:: python

        @app.route('/profile', method=['GET'])
        @authorize.self(User.current)
        def get_profile():
            return

        @app.route('/users/<id(User):user>', method=['GET'])
        @authorize.read
        def get_user(user):
            return

        @app.route('/users/<id(User):user>', method=['PUT'])
        @authorize.update
        @authorize.role('user-updators')
        def update_user(user):
            return

        @app.route('/users/<ident>', method=['PUT'])
        def update_user(ident):
            user = User.get(id=ident)
            if not authorize.update(user) or not authorize.role('test-role'):
                raise Unauthorized
            return


    """

    def __init__(self, permit=None, roles=[]):
        # TODO
        # parse permit
        # -- EITHER NONE, 6, 'rw', 'r', etc ..
        # TODO: NEED TO FIGURE OUT HOW TO GET MUTLI-DECORATOR SET UP GOING
        #       NOTE - FIGURE OUT HOW TO RE-DECORATE WITH SAME CLASS AND
        #       UPDATED PARAMS
        self.permit = permit
        if not isinstance(roles, (list, tuple)):
            roles = [roles]
        self.roles = roles
        return

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
                permit=original.permit | self.permit,
                roles=original.roles + self.roles
            )
            AUTHORIZE_CACHE[func.__name__] = updated
            del original

        auth = AUTHORIZE_CACHE[func.__name__]

        @wraps(func)
        def inner(*args, **kwargs):
            # gather all items to check authorization for
            check = list(args) + list(kwargs.values())

            # check if authorized
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
            return False

        # authorize if user is part of role
        if hasattr(user, 'roles'):
            for role in user.roles:
                if role.name in self.roles:
                    return True

        # check permissions on individual instances
        for arg in args:

            # only check permissions for items that have set permissions
            if not isinstance(arg.__class__, six.class_types):
                continue
            if not hasattr(arg, 'permissions'):
                continue

            # configure individual permissions
            owner = int(arg.permissions) // 10**2 % 10
            group = int(arg.permissions) // 10**1 % 10
            other = int(arg.permissions) // 10**0 % 10

            # check other permissions
            if other & self.permit:
                return True

            # check user permissions
            if hasattr(arg, 'owner'):
                if arg.owner == user:
                    if owner & self.permit:
                        return True

            # check group permissions
            if hasattr(arg, 'group'):
                if hasattr(user, 'groups'):
                    if arg.group in user.groups:
                        if group & self.permit:
                            return True
        return False
