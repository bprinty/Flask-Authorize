# -*- coding: utf-8 -*-

__pkg__ = 'Flask-Authorize'
__url__ = 'https://github.com/bprinty/Flask-Authorize'
__info__ = 'Flask plugin for managing content access authorization'
__author__ = 'Blake Printy'
__email__ = 'bprinty@gmail.com'
__version__ = '0.1.0'


from .mixins import PermissionsMixin  ## noqa
from .plugin import Authorize         ## noqa
