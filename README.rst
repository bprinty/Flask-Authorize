
|Build status| |Code coverage| |Maintenance yes| |GitHub license| |Documentation Status|

.. |Build status| image:: https://travis-ci.com/bprinty/Flask-Authorize.png?branch=master
   :target: https://travis-ci.com/bprinty/Flask-Authorize

.. |Code coverage| image:: https://codecov.io/gh/bprinty/Flask-Authorize/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/bprinty/Flask-Authorize

.. |Maintenance yes| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
   :target: https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity

.. |GitHub license| image:: https://img.shields.io/github/license/Naereen/StrapDown.js.svg
   :target: https://github.com/bprinty/Flask-Authorize/blob/master/LICENSE

.. |Documentation Status| image:: https://readthedocs.org/projects/flask-authorize/badge/?version=latest
   :target: http://flask-authorize.readthedocs.io/?badge=latest


============================
Flask-Authorize
============================

Flask-Authorize is a Flask extension designed to simplify the process of incorporating Access Control Lists (ACLs) and Role-Based Access Control (RBAC) into applications housing sensitive data, allowing developers to focus on the actual code for their application instead of logic for enforcing permissions. It uses a unix-like permissions scheme for enforcing access permissions on existing content, and also provides mechanisms for globally enforcing permissions throughout an application.


Installation
============

To install the latest stable release via pip, run:

.. code-block:: bash

    $ pip install Flask-Authorize


Alternatively with easy_install, run:

.. code-block:: bash

    $ easy_install Flask-Authorize


To install the bleeding-edge version of the project (not recommended):

.. code-block:: bash

    $ git clone http://github.com/bprinty/Flask-Authorize.git
    $ cd Flask-Authorize
    $ python setup.py install


Usage
=====

Below details a minimal example showcasing how to use the extension. First, to set up the flask application with extensions:


.. code-block:: python

    from flask import Flask
    from flask_login import LoginManager
    from flask_sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    app.config.from_object(Config)
    db = SQLAlchemy(app)
    login = LoginManager(app)
    authorize = Authorize(app)


Defining database models:

.. code-block:: python

    from flask_authorize import RestrictionsMixin, AllowancesMixin
    from flask_authorize import PermissionsMixin


    # mapping tables
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


    # models
    class User(db.Model):
        __tablename__ = 'users'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)

        # `roles` and `groups` are reserved words that *must* be defined
        # on the `User` model to use group- or role-based authorization.
        roles = db.relationship('Role', secondary=UserRole)
        groups = db.relationship('Group', secondary=UserGroup)


    class Group(db.Model, RestrictionsMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)


    class Role(db.Model, AllowancesMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)


    class Article(db.Model, PermissionsMixin):
        __tablename__ = 'articles'
        __permissions__ = dict(
            owner=['read', 'update', 'delete', 'revoke'],
            group=['read', 'update'],
            other=['read']
        )

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), index=True, nullable=False)


Defining endpoint actions:

.. code-block:: python
    
    from flask import jsonify
    from werkzeug import NotFound, Unauthorized

    @app.route('/articles', methods=['POST'])
    @login.logged_in
    @authorize.create(Article)
    def article():
        article = Article(**request.json)
        db.session.add(article)
        db.session.commit()
        return jsonify(msg='Created Article'), 200

    @app.route('/articles/<int:ident>', methods=['GET', 'PUT', 'DELETE'])
    @login.logged_in
    def single_article(ident):
        article = db.session.query(Article).filter_by(id=ident).first()
        if not article:
            raise NotFound

        if request.method == 'GET':

            # check if the current user is authorized to read the article
            if not authorize.read(article):
                raise Unauthorized

            return jsonify(id=article.id, name=article.name), 200

        elif request.method == 'PUT':

            # check if the current user is authorized to update to the article
            if not authorize.update(article):
                raise Unauthorized

            for key, value in request.json.items():
                setattr(article, key, value)
            db.session.commit()

            return jsonify(id=article.id, name=article.name), 200

        elif request.method == 'DELETE':

            # check if the current user is associated with the 'admin' role
            if not authorize.delete(article) or \
               not authorize.has_role('admin'):
                raise Unauthorized

            db.session.delete(article)
            db.session.commit()

        return

    @app.route('/articles/<int:ident>/revoke', methods=['POST'])
    @login.logged_in
    def revoke_article(ident):
        article = db.session.query(Article).filter_by(id=ident).first()
        if not article:
            raise NotFound

        # check if the current user can revoke the article
        if not authorize.revoke(article):
            raise Unauthorized

        article.revoked = True
        db.session.commit()

        return


Additionally, if you've configured your application to dispatch request processing to API functions, you can use the ``authorize`` extension object as a decorator:

.. code-block:: python

    @authorize.create(Article)
    def create_article(name):
        article = Article(**request.json)
        db.session.add(article)
        db.session.commit()
        return article

    @authorize.read
    def read_article(article):
        return article

    @authorize.update
    def update_article(article, **kwargs):
        for key, value in request.json.items():
            setattr(article, key, value)
        db.session.commit()
        return article

    @authorize.delete
    def delete_article(article):
        db.session.delete(article)
        return

    @authorize.revoke
    def revoke_article(article):
        article.revoke = True
        db.session.commit()
        return

    @authorize.has_role('admin')
    def get_admin_articles():
        pass


Using the extension as a decorator goes a long way in removing boilerplate associated with permissions checking. Additionally, using the ``authorize`` extension object as a decorator will implicitly check the current user's access to each argument or keyword argument to the function. For example, if your method takes two ``Article`` objects and merges them into one, you can add permissions for both operations like so:

.. code-block:: python

    @authorize.read
    @authorize.create(Article)
    def merge_articles(article1, article2):
        new_article = Article(name=article1.name + article.2.name)
        db.session.add(new_article)
        db.session.delete(article1, article2)
        db.session.commit()
        return new_article


This function will ensure that the current user has read access to both articles and also create permissions on the **Article** model itself. If the authorization criteria aren't satisfied, an ``Unauthorized`` error will be thrown.

Finally, the ``authorize`` operator is also available in Jinja templates:

.. code-block:: html

    <!-- button for creating new article -->
    {% if authorize.create('articles') %}
        <button>Create Article</button>
    {% endif %}

    <!-- display article feed -->
    {% for article in articles %}

        <!-- show article if user has read access -->
        {% if authorize.read(article) %}
            <h1>{{ article.name }}</h1>

            <!-- add edit button for users who can update-->
            {% if authorize.update(article) %}
                <button>Update Article</button>
            {% endif %}

            <!-- add delete button for administrators -->
            {% if authorize.in_group('admins') %}
                <button>Delete Article</button>
            {% endif %}

        {% endif %}
    {% endfor %}


Documentation
=============

For more detailed documentation, see the `Docs <https://Flask-Authorize.readthedocs.io/en/latest/>`_.


Questions/Feedback
==================

File an issue in the `GitHub issue tracker <https://github.com/bprinty/Flask-Authorize/issues>`_.
