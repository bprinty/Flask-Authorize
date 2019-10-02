
Overview
========

Something something ... This simplifies the boilerplate each method requires to enforce permissions, allowing developers to simply focus on code.



A Minimal Application
---------------------


Setting up the flask application with extensions:


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

    from flask_authorize import UserAuthMixin, GroupAuthMixin, RoleAuthMixin
    from flask_authorize import PermissionsMixin

    class User(db.Model, UserAuthMixin):
        __tablename__ = 'users'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)


    class Group(db.Model, GroupAuthMixin):
        pass

    class Role(db.Model, RoleAuthMixin):
        pass


    class Article(db.Model, PermissionsMixin):
        __tablename__ = 'articles'
        __permissions__ = '666'

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
    def article(ident):
        article = db.session.query(Article).filter_by(id=ident).first()
        if not article:
            raise NotFound

        if request.method == 'GET':

            # check if the current user is authorized to read the article
            if not authorize.read(article):
                raise Unauthorized

            return jsonify(id=article.id, name=article.name), 200

        elif request.method == 'PUT':

            # check if the current user is authorized to write to the article
            if not authorize.write(article):
                raise Unauthorized

            for key, value in request.json.items():
                setattr(article, key, value)
            db.session.commit()

            return jsonify(id=article.id, name=article.name), 200

        elif request.method == 'DELETE':

            # check if the current user is associated with the 'admin' role
            if not authorize.has_role('admin'):
                raise Unauthorized

            db.session.delete(article)
            db.session.commit()

        return


Additionally, if you've configured your application to dispatch request to api functions, you can use the ``authorize`` extension object as a decorator:

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

    @authorize.write
    def update_article(article, **kwargs):
        for key, value in request.json.items():
            setattr(article, key, value)
        db.session.commit()
        return article

    @authorize.delete
    def delete_article(article):
        db.session.delete(article)
        return

    @authorize.role('admin')
    def get_admin_articles():
        pass


Using the ``authorize`` extension object as a decorator will implicitly check the current user's access to each argument or keyword argument to the function. For example, if your method takes two `Article` objects and merges them into one, you can add permissions for both operations like so:

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


Usage without Flask-Login
-------------------------

By default, this module uses the Flask-Login extension for determining the current user. If you aren't using that module, you simply need to provide a function to the plugin that will return the current user:

.. code-block:: python

    from flask import Flask
    from flask_authorize import Authorize

    def my_current_user():
        # logic to get user for authorization
        return user

    # using the declarative method for setting up the extension
    app = Flask(__name__)
    authorize = Authorize(current_user=my_current_user)
    authorize.init_app(app)


For more in-depth discussion on design considerations and how to fully utilize the plugin, see the `User Guide <./usage.html>`_.
