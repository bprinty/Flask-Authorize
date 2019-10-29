# -*- coding: utf-8 -*-
#
# Fixtures for administration.
#
# ------------------------------------------------


# imports
# -------
import pytest
import factory
from flask import Flask, request, jsonify, g
from werkzeug.exceptions import Unauthorized, NotFound
from flask_sqlalchemy import SQLAlchemy
from flask_authorize import Authorize, PermissionsMixin, AllowancesMixin, RestrictionsMixin
from flask_authorize.mixins import default_allowances, default_restrictions

from . import SANDBOX


# application
# -----------
class Config(object):
    ENV = 'testing'
    TESTING = True
    SQLALCHEMY_ECHO = False
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/app.db'.format(SANDBOX)


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
authorize = Authorize(app, current_user=lambda: g.user)


# models
# ------
UserGroup = db.Table(
    'user_group', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'))
)


UserRole = db.Table(
    'user_role', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    roles = db.relationship('Role', secondary=UserRole)
    groups = db.relationship('Group', secondary=UserGroup)


class Group(db.Model, RestrictionsMixin):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    desc = db.Column(db.String(255))
    users = db.relationship('User', secondary=UserGroup)


class Role(db.Model, AllowancesMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    desc = db.Column(db.String(255))
    users = db.relationship('User', secondary=UserRole)


class Article(db.Model, PermissionsMixin):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, nullable=False)


# factories
# ---------
class GroupFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')

    class Meta:
        model = Group
        sqlalchemy_session = db.session


class RoleFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')

    class Meta:
        model = Role
        sqlalchemy_session = db.session


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')

    class Meta:
        model = User
        sqlalchemy_session = db.session


class ArticleFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')
    owner = factory.SubFactory(UserFactory)

    class Meta:
        model = Article
        sqlalchemy_session = db.session


# fixtures
# --------
@pytest.fixture(scope='session')
def users(client):

    # roles
    admin = RoleFactory.create(name='admin')

    # groups
    editors = GroupFactory.create(name='editors')
    readers = GroupFactory.create(name='readers')

    # users
    admin = UserFactory.create(
        name='admin',
        roles=[admin]
    )
    editor = UserFactory.create(
        name='editor',
        groups=[readers, editors]
    )
    reader = UserFactory.create(
        name='reader',
        groups=[readers]
    )
    users = [admin, editor, reader]

    from flask import g
    g.user = admin

    yield users

    return


def allowed(client):
    role = RoleFactory.create(
        name='allowed',
        allowances=default_allowances()
    )
    yield UserFactory.create(
        name='allowed',
        roles=[role]
    )


def unallowed(client):
    role = RoleFactory.create(
        name='unallowed',
        allowances={}
    )
    yield UserFactory.create(
        name='unallowed',
        roles=[role]
    )


def restricted(client):
    group = GroupFactory.create(
        name='restricted',
        restrictions={'articles': default_allowances()}
    )
    yield UserFactory.create(
        name='restricted',
        roles=[group]
    )


def unrestricted(client):
    group = GroupFactory.create(
        name='unrestricted',
        restrictions={'articles': default_restrictions()}
    )
    yield UserFactory.create(
        name='unrestricted',
        roles=[group]
    )
