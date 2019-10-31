# -*- coding: utf-8 -*-
#
# Pytest configuration
#
# ------------------------------------------------


# imports
# -------
import os
import pytest
import logging

from flask import g
from .fixtures import db, app


# config
# ------
SETTINGS = dict(
    teardown=True,
    echo=False,
)
APP = None
CLIENT = None
logging.basicConfig(level=logging.ERROR)


# plugins
# -------
pytest_plugins = [
    'tests.fixtures'
]


def pytest_addoption(parser):
    parser.addoption("-N", "--no-teardown", default=False, help="Do not tear down sandbox directory after testing session.")
    parser.addoption("-E", "--echo", default=False, help="Be verbose in query logging.")
    return


def pytest_configure(config):
    global TEARDOWN
    SETTINGS['teardown'] = not config.getoption('-N')
    SETTINGS['echo'] = config.getoption('-E')
    return


@pytest.fixture(autouse=True, scope='session')
def application(request):
    from . import SANDBOX
    global SETTINGS, APP, CLIENT

    # create sandbox for testing
    if not os.path.exists(SANDBOX):
        os.makedirs(SANDBOX)

    # create application
    if SETTINGS['echo']:
        app.config['SQLALCHEMY_ECHO'] = True

    # create default user
    with app.app_context():
        g.user = None
        db.drop_all()
        db.create_all()
        yield app

    # teardown sandbox
    if SETTINGS['teardown']:
        import shutil
        shutil.rmtree(SANDBOX)
    return


@pytest.fixture(scope='session')
def client(application):
    global CLIENT
    if CLIENT is not None:
        yield CLIENT
    else:
        with app.test_client() as CLIENT:
            yield CLIENT
    return
