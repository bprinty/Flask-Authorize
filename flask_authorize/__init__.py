# -*- coding: utf-8 -*-

__pkg__ = 'Flask-Authorize'
__url__ = 'https://github.com/bprinty/Flask-Authorize'
__info__ = 'Flask plugin for content authorization and access control'
__author__ = 'Blake Printy'
__email__ = 'bprinty@gmail.com'
__version__ = '0.1.8'


from .mixins import RestrictionsMixin           ## noqa
from .mixins import AllowancesMixin             ## noqa

from .mixins import OwnerPermissionsMixin       ## noqa
from .mixins import GroupPermissionsMixin       ## noqa
from .mixins import PermissionsMixin            ## noqa

from .mixins import default_permissions         ## noqa
from .mixins import default_allowances          ## noqa
from .mixins import default_restrictions        ## noqa

from .plugin import Authorize                   ## noqa
