#!/usr/bin/env python
#
# File used for debugging issues.
#
# -----------------------------------------


# imports
# -------
import os
from flask import Flask, render_template, g, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from flask_authorize import Authorize, PermissionsMixin, AllowancesMixin, RestrictionsMixin
from flask_authorize.mixins import default_allowances, default_restrictions, default_permissions


# application
# -----------
class Config(object):
    ENV = 'testing'
    TESTING = True
    SQLALCHEMY_ECHO = False
    SECRET_KEY = '67yuhj'
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/app.db'.format(os.getcwd())
    AUTHORIZE_ALLOW_ANONYMOUS_ACTIONS = True


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
authorize = Authorize(app)


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


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    # __check_access__ = False

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    roles = db.relationship('Role', secondary=UserRole)
    groups = db.relationship('Group', secondary=UserGroup)


class Group(db.Model, RestrictionsMixin):
    __tablename__ = 'groups'
    # __check_access__ = False

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    users = db.relationship('User', secondary=UserGroup)


class Role(db.Model, AllowancesMixin):
    __tablename__ = 'roles'
    # __check_access__ = False

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    users = db.relationship('User', secondary=UserRole)


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, nullable=False)


# routes
# ------
@app.route('/register')
def register():
    """
    Register new user with specified roles and groups.
    """
    if 'name' not in request.args:
        raise AssertionError('Name argument must be in request.')

    # create user
    q = User.query.filter_by(name=request.args['name']).first()
    if q:
        user = q
    else:
        user = User(name=request.args['name'])
    db.session.add(user)
    db.session.flush()

    # configure roles
    roles = []
    for role in request.args.get('roles', 'default').split(','):
        q = Role.query.filter_by(name=role).first()
        if q:
            roles.append(q)
        else:
            roles.append(Role(name=role))
        db.session.add(roles[-1])
        user.roles.append(roles[-1])
        db.session.flush()

    # configure  groups
    groups = []
    for group in request.args.get('groups', 'default').split(','):
        q = Group.query.filter_by(name=group).first()
        if q:
            groups.append(q)
        else:
            groups.append(Group(name=group))
        db.session.add(groups[-1])
        user.groups.append(groups[-1])
        db.session.flush()
    db.session.commit()
    return jsonify({ 'status': 'ok' })


@app.route('/login')
def login():
    """
    Get metadata about current user.
    """
    if 'name' not in request.args:
        raise AssertionError('Name argument must be in request.')
    user = User.query.filter_by(name=request.args['name']).one()
    login_user(user)
    return jsonify({ 'status': 'ok' })


@app.route('/profile')
def profile():
    """
    Get metadata about current user.
    """
    if current_user.is_anonymous:
        return jsonify({})
    return jsonify(dict(
        name=current_user.name,
        roles=[role.name for role in current_user.roles],
        groups=[group.name for group in current_user.groups]
    ))


@app.route('/role-default')
@login_required
@authorize.has_role('default')
def authorize_role_default():
    return jsonify({ 'status': 'ok' })


@app.route('/role-admin')
@login_required
@authorize.has_role('admin')
def authorize_role_admin():
    return jsonify({ 'status': 'ok' })



# setup
# -----
@app.before_first_request
def create_tables():
    db.create_all()
    return


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()
