# -*- coding: utf-8 -*-
#
# Fixtures for administration.
#
# ------------------------------------------------


# imports
# -------
import pytest
import factory
from flask import Flask, render_template, g
from flask_sqlalchemy import SQLAlchemy
from flask_authorize import Authorize, PermissionsMixin, AllowancesMixin, RestrictionsMixin
from flask_authorize.mixins import default_allowances, default_restrictions, default_permissions

from . import SANDBOX


# application
# -----------
class Config(object):
    ENV = 'testing'
    TESTING = True
    SQLALCHEMY_ECHO = False
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/app.db'.format(SANDBOX)
    AUTHORIZE_ALLOW_ANONYMOUS_ACTIONS = True


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
    __check_access__ = False

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    roles = db.relationship('Role', secondary=UserRole)
    groups = db.relationship('Group', secondary=UserGroup)


class Group(db.Model, RestrictionsMixin):
    __tablename__ = 'groups'
    __check_access__ = False

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    desc = db.Column(db.String(255))
    users = db.relationship('User', secondary=UserGroup)


class Role(db.Model, AllowancesMixin):
    __tablename__ = 'roles'
    __check_access__ = False

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    desc = db.Column(db.String(255))
    users = db.relationship('User', secondary=UserRole)


class Article(db.Model, PermissionsMixin):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, nullable=False)


# endpoints
# ---------
@app.route('/feed', methods=['GET'])
def feed():
    articles = Article.query.filter_by(name='Jinja Article').all()
    return render_template('feed.html', articles=articles)


# factories
# ---------
class GroupFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')

    class Meta:
        model = Group
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'


class RoleFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')

    class Meta:
        model = Role
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')

    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'


class ArticleFactory(factory.alchemy.SQLAlchemyModelFactory):

    id = factory.Sequence(lambda x: x + 100)
    name = factory.Faker('name')
    owner = factory.SubFactory(UserFactory)
    permissions = factory.LazyFunction(default_permissions)

    class Meta:
        model = Article
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'


# fixtures
# --------
@pytest.fixture(scope='session')
def anonymous(client):
    yield UserFactory.create(
        name='anonymous'
    )


@pytest.fixture(scope='session')
def admin(client):
    group = GroupFactory.create(name='admins')
    role = RoleFactory.create(name='admins')
    yield UserFactory.create(
        name='admin',
        groups=[group],
        roles=[role]
    )


@pytest.fixture(scope='session')
def reader(client):
    group = GroupFactory.create(name='readers')
    role = RoleFactory.create(name='readers')
    yield UserFactory.create(
        name='reader',
        groups=[group],
        roles=[role]
    )


@pytest.fixture(scope='session')
def editor(client):
    group = GroupFactory.create(name='editors')
    role = RoleFactory.create(name='editors')
    yield UserFactory.create(
        name='editor',
        groups=[group],
        roles=[role]
    )


@pytest.fixture(scope='session')
def allowed(client):
    role = RoleFactory.create(
        name='allowed',
        allowances=default_allowances()
    )
    yield UserFactory.create(
        name='allowed',
        roles=[role]
    )


@pytest.fixture(scope='session')
def unallowed(client):
    role = RoleFactory.create(
        name='unallowed',
        allowances={}
    )
    yield UserFactory.create(
        name='unallowed',
        roles=[role]
    )


@pytest.fixture(scope='session')
def restricted(client):
    group = GroupFactory.create(
        name='restricted',
        restrictions=default_allowances()
    )
    yield UserFactory.create(
        name='restricted',
        groups=[group]
    )


@pytest.fixture(scope='session')
def unrestricted(client):
    group = GroupFactory.create(
        name='unrestricted',
        restrictions=default_restrictions()
    )
    yield UserFactory.create(
        name='unrestricted',
        groups=[group]
    )
