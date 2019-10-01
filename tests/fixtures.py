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
from flask_authorize import Authorize, PermissionsMixin

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


@app.route('/articles', methods=['GET', 'POST'])
def articles():
    if request.method == 'GET':
        if not authorize.read(Article):
            return Unauthorized
        articles = db.session.query(Article).all()
        return jsonify([dict(id=a.id, name=a.name) for a in articles]), 200

    elif request.method == 'POST':
        if not authorize.write(Article):
            return Unauthorized
        article = Article(**request.json)
        db.session.add(article)
        db.session.commit()
        return jsonify(id=article.id, name=article.name), 200

    return


@app.route('/articles/<int:ident>', methods=['GET', 'PUT', 'DELETE'])
def single_article(ident):
    article = db.session.query(Article).filter_by(id=ident).first()
    if not article:
        raise NotFound
    if request.method == 'GET':
        if not authorize.read(article):
            raise Unauthorized
        return jsonify(id=article.id, name=article.name), 200

    elif request.method == 'PUT':
        if not authorize.write(article):
            raise Unauthorized
        for key, value in request.json.items():
            setattr(article, key, value)
        db.session.commit()
        return jsonify(id=article.id, name=article.name), 200

    elif request.method == 'DELETE':
        if not authorize.has_role('admin'):
            raise Unauthorized
        db.session.delete(article)
        db.session.commit()

    return


@authorize.read
def get_article(article):
    return dict(
        id=article.id,
        name=article.name
    )


@authorize.write
def update_article(article, **kwargs):
    for k, v in kwargs.items():
        setattr(article, k, v)
    db.session.commit()
    return dict(
        id=article.id,
        name=article.name
    )


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

    # basic
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)

    # relationships
    roles = db.relationship('Role', secondary=UserRole)
    groups = db.relationship('Group', secondary=UserGroup)


class Group(db.Model):
    __tablename__ = 'groups'

    # basic
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    desc = db.Column(db.String(255))
    # restrictions = db.Column(db.JSON, nullable=False)

    # relationships
    users = db.relationship('User', secondary=UserGroup)


class Role(db.Model):
    __tablename__ = 'roles'

    # basic
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    desc = db.Column(db.String(255))
    # restrictions = db.Column(db.JSON, nullable=False)

    # relationships
    users = db.relationship('User', secondary=UserRole)


class Article(db.Model, PermissionsMixin):
    __tablename__ = 'articles'
    __permissions__ = '666'

    # basic
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
