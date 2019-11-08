
Usage
=====

The sections below detail how to fully use this module, along with context for design decisions made during development of the plugin.


Access Control
--------------

Applications housing sensitive material are often required to restrict certain types of access to both content and actions related to that content. This means that developers of the application need the ability to either permit or deny:

* Creation of new content.
* Read access to existing content.
* Updates to existing content.
* Deletion of existing content.
* Other customized specific actions on existing content.

Moreover, there are several mechanisms for assigning permissions to users of the application:

* Role-based access control via permissions or restrictions (RBACs).
* Group-based access control via permissions or restrictions.
* Access rights for existing content via owner/group(s) and permission schemes (ACLs).

This package tries to accommodate each of these needs, providing a flexible set of tools to fit alongside all of these authorization schemes. The flexibility of this plugin allows developers to only use what their application requires.


Users, Roles, Groups
--------------------

With any authorization mechanism, you need an entity to authorize against. In standard web applications, there are three types of entities that are typically authorized against: the ``User``, ``Group``, and ``Role``. To understand the nuances of each model, let's go over the purpose of each.

* User: A user represents a singular entity that is interacting with the application. They can assume multiple roles or be part of multiple groups.

* Role: A role represents an identity that a user can take while performing certain actions in the application. Roles are typically associated with permissions or permission restrictions.

* Group: A group represents a collection of users. Groups can be associated with permissions or permission restrictions.


Let's use a basketball analogy to make things more concrete. In this analogy, examples of each model are as follows:

* Users: MJ, Scottie Pippen, Dennis Rodman, Toni Kukoc, Steve Kerr, Robert Parish

* Roles: Shooting Guard, Small Forward, Power Forward, Point Guard

* Group: Bulls, Team Captains, Scorers, Role-Players

In this analogy, there are a multitude of actions that can be performed by any of these entities. However, only certain entities should be allowed to do certain things. For example, in this analogy:

* A user assuming the role 'Small Forward' (Rodman) shouldn't be able to perform the action 'shoot 3s'.

* A user in the group 'Bulls' shouldn't perform the action 'score for the Jazz'.

In addition, you might need to restrict access to certain types of created content in the application to specific users or groups. Using a playbook as a content example, you might want to say that everyone in the 'Bulls' group can read the playbook, but only members of the 'Team Captains' group can make edits to it. We could go down this analogy further, but let's switch context to a more relevant use case.


A Relevant Use-Case
-------------------

In the documentation below, we need a use-case to illustrate the various functionality this plugin provides. Let's use the following models in the examples throughout the rest of the documentation.

* ``User`` - The current logged-in user issuing a request.
* ``Group`` - A collection of users. The current user can be assigned to one or multiple groups.
* ``Role`` - A vehicle for assigning permissions. The current user can be allowed to take on one or multiple roles.
* ``Article`` - A piece of content that needs to potentially have both RBAC and ACL enforcement.

Here are model definitions for the above scheme in the context of a Flask application:

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
            contents = db.Column(db.Text)


.. note:: Not all of these models are necessary for using this plugin. For example: if your application doesn't need Role-based authentication, you don't need to define a `Role` model in your database.


What's actually necessary?
--------------------------

It really depends on how you want to structure your application. If your application requires only owner or other content restrictions, you don't need to configure a ``Group`` or ``Role`` model for this plugin to work. if your application doesn't need the additional role authorization, you don't need to configure a ``Role`` to use with the plugin.

The important thing to understand is that there are two reserved keywords on the ``User`` model (the object returned by the ``current_user`` function configured for the plugin): ``roles`` and ``groups``. These need to be configured to return (respectively) a list of ``Role`` or ``Group`` objects to check authorization for if your application is configured to do role- or group-based authorization. Here's an example of a correctly configured user model (``UserRole`` and ``UserGroup`` are separate mapping tables).

.. code-block:: python

    class User(db.Model):
        __tablename__ = 'users'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)

        # `roles` and `groups` are reserved words that *must* be defined
        # on the `User` model to use group- or role-based authorization.
        roles = db.relationship('Role', secondary=UserRole)
        groups = db.relationship('Group', secondary=UserGroup)


This application will implicitly check the existence of ``roles`` and ``groups`` properties on the current user object when checking authorization. If either of these properties is not defined, this plugin will not perform associated authorization checks.


Content Permissions
-------------------

Permissions administration for this plugin was inspired by Filesystem ACLs in Linux, where content (files) are associated with three things: an owner, a group, and a set of permissions. For each content model you want to restrict access to, you can define permissions like so:

.. code-block:: python

    class Article(db.Model, PermissionsMixin):
        pass


This uses default content permissions taken from the ``AUTHORIZE_DEFAULT_PERMISSIONS`` configuration variable. If you want to customize content permissions, you can set the value of the ``__permissions__`` property:

.. code-block:: python

    class Article(db.Model, PermissionsMixin):
        __permissions__ = dict(
            owner=['read', 'update', 'delete'],
            group=['read', 'update'],
            other=['read']
        )


This explicit syntax is designed to allow for more customized authorization schemes. For the `Article` example, to add a permission specific to `revoke`-ing an article, you can configure the permissions like so:

.. code-block:: python

    class Article(db.Model, PermissionsMixin):
        __permissions__ = dict(
            owner=['read', 'update', 'delete', 'revoke'], # owners can revoke
            group=['read', 'update', 'revoke'], # group can revoke
            other=['read']
        )

And once you've done that, you can use the `@authorize.action` decorator with the name of the permission:

.. code-block:: python

    @authorize.revoke
    def revoke_article(article):
        # only those with access to revoke are allowed
        pass


For developers who enjoy assigning permissions via numeric schemes (à la Unix systems), that is also covered:

.. code-block:: python

    class Article(db.Model, PermissionsMixin):
        __permissions__ =  764  # owner (read, update, delete)
                                # group (read, update)
                                # other (read)


.. note:: Numeric permissions schemes are only supported for restricting read, update, and delete permissions on created content. Bit masks are as follows: 1 (0b001): delete, 2 (0b010): read, 4 (0b100): update. Custom permission schemes must explicitly state permission names.


Setting Custom Content Permissions
----------------------------------

If you want to override default permissions for a piece of content, you can do so with the ``set_permissions`` method on a content object:

.. code-block:: python

    article = Article(
        name='test'
    )
    article.set_permissions(
        group=['read', 'update']  # read and update
        other=2                   # read
    )

Alternatively, using a numeric scheme:

.. code-block:: python

    article = Article(
        name='test'
    )
    article.set_permissions(762)


Additionally, permissions can be accessed with the ``permissions`` property on a content object:

.. code-block:: python

    >>> article = Article(name='test')
    >>> print(article.permissions)
    {
        'owner': ['read', 'update', 'delete'],
        'group': ['read', 'update'],
        'other': ['read']
    }


Restrictions
------------

In addition to authorizing permissions on created content, we can also add another layer of authorization with ``Role`` or ``Group`` content restrictions. With content restrictions, users in associated roles or groups will be unauthorized to perform specific actions. To configure your roles or groups to enable restrictions, you can use the ``RestrictionsMixin`` object:

.. code-block:: python

    class Role(db.Model, RestrictionMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)

    class Group(db.Model, RestrictionMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)


Once configured with this mixin, restrictions can be set up for users like so:

.. code-block:: python

    # create user and associated role
    role = Role(
        name='reader',
        restrictions=dict(
            articles=['create', 'update', 'delete'],
            secret_articles=['create', 'read', 'update', 'delete']
        )
    )
    user = User(name='User 1')
    user.roles = [role]
    db.session.add(role, user)
    db.session.commit()


Once this is all configured, you can enforce these restrictions like so:

.. code-block:: python

    # via decoration
    @authorize.create(Article)
    def create_article(name):
        # will raise an Unauthorized error if the user
        # is not authorized to create articles
        pass

    @authorize.update
    @authorize.in_group('admin-editors')
    def update_article(name):
        # will raise an Unauthorized error if the user
        # is not authorized to update articles or is
        # not in the group 'admin-editors'
        pass

    @authorize.delete
    @authorize.has_role('admin')
    def delete_article(name):
        # will raise an Unauthorized error if the user
        # is not an admin or not authorized to delete articles
        pass


    # directly
    def get_article(name):
        article = session.query(Article).filter_by(name=name).first()
        if not article:
            raise NotFound

        # check if the current user has no read access restrictions
        if not authorize.read(article):
            raise Unauthorized
        return article


Even if your content permissions are configured to be wide open, user role/group restrictions will still be checked when determining access.

.. note:: In cases where both Role/Group restrictions and content permissions are conflicting, the most stringent set of permissions will be used. For example, if a user is configured with update restrictions to all `Article` objects and has update access via `Article` permissions, they will be unauthorized to update that content.


Allowances
----------

If you want to explicitly allow access to each type of action (i.e. the inverse of **restrictions**), you can do so using the ``RoleAllowancesMixin`` and ``GroupAllowancesMixin`` mixin objects when defining your models. See the `Database Mixins`_ section below for more details on what each of the mixins provide.

Mirroring the example above, we can explicitly set allowances for a role via:

.. code-block:: python

    role = Role(
        name='reader',
        allowances=dict(
            articles='r'          # read only authorization
            secret_articles=None  # no authorization
        )
    )
    db.session.add(role)
    db.session.commit()

.. note:: In cases where both Role/Group allowances and content permissions are conflicting, the most stringent set of permissions will be used. For example, if a user is configured with read access to all `Article` objects but doesn't have access via `Article` permissions, they will be unauthorized to view that content.


Authorization Schemes
---------------------

authorize.<action>
+++++++++++++++++++

Methods under this authorization scheme:

    * ``authorize.read``
    * ``authorize.update``
    * ``authorize.delete``
    * ``authorize.create(ContentModel)``
    * ``authorize.custom_scheme``

Return ``True`` if the ``current_user`` is authorized to access content either by content permissions or by Group- or Role- based permissions or restrictions. Since this type of permissions scheme includes both content permissions and potential Role/Group restrictions or permissions, let's go over logical flow in two stages. First, role- or group-based access control:

1. Is the user assuming a role or have a role that does not allow access (restrictions)? (if applicable)
2. Is the user assuming a role or have a role that does not include access in allowances? (if applicable)
3. Is the user in a group that does not allow access? (if applicable)
4. Is the user in a group that does not include access in allowances? (if applicable)

If any of these criteria are met, the authorization scheme will return ``False``. Now for access control lists related to the specific content item:

5. For the specific content item, does the ``other`` permissions component allow access?
6. For the specific content item, does the ``owner`` permissions component allow access?
7. For the specific content item, does the ``group`` permissions component allow access?

If any of these criteria are not met, the authorization scheme will return ``False``.

Below is an example of how this scheme might be used:

.. code-block:: python

    # decoration
    @authorize.create(Article)
    def create_article(name):
        # raise Unauthorized if the `current_user` is not
        # authorized to create the article
        pass

    @authorize.read
    def get_article(article):
        # raise Unauthorized if the `current_user` is not
        # authorized to read the article
        pass

    @authorize.update
    def update_article(article):
        # raise Unauthorized if the `current_user` is not
        # authorized to update the article
        pass

    @authorize.delete
    def update_article(article):
        # raise Unauthorized if the `current_user` is not
        # authorized to delete the article
        pass

    @authorize.revoke
    def revoke_article(article):
        # raise Unauthorized if the `current_user` is not
        # authorized to revoke the article. In this example,
        # `revoke` is a custom authorization scheme. 
        pass

    # explicit
    def all_article_actions(article):
        if not authorize.create(article.__class__) or \
           not authorize.read(article) or \
           not authorize.update(article) or \
           not authorize.delete(article) or \
           not authorize.revoke(article):
            raise Unauthorized
        pass

This authorization mechanism can be used in conjunction with content models using the ``PermissionsMixin`` or ``MultiGroupPermissionsMixin``.


authorize.in_group('<group>')
+++++++++++++++++++++++++++++

Return ``True`` if the ``current_user`` is not associated with the specified ``Group``. For example:

.. code-block:: python

    # decorator
    @authorize.in_group('administrators')
    def admin_func(article):
        # raise Unauthorized if the `current_user` is not in
        # the `administrators` group.
        pass

    # explicit
    def admin_handler(article):
        if not authorize.in_group('administrators'):
            raise Unauthorized
        pass


authorize.has_role('<role>')
++++++++++++++++++++++++++++

Return ``True`` if the ``current_user`` is not associated with the specified ``Role``. For example:

.. code-block:: python

    # decorator
    @authorize.has_role('admin')
    def admin_func(article):
        # raise Unauthorized if the `current_user` is not associated
        # with the `admin` role.
        pass

    # explicit
    def admin_handler(article):
        if not authorize.has_role('admin'):
            raise Unauthorized
        pass


.. authorize.is_role('<role>')
.. +++++++++++++++++++++++++++

.. Return ``True`` if the ``current_user`` has a ``current_role`` property that matches the specified ``Role``. For example:

.. .. code-block:: python

..     # decorator
..     @authorize.is_role('admin')
..     def admin_func(article):
..         # raise Unauthorized if the `current_user` is not
..         # assuming the `admin` role.
..         pass

..     # explicit
..     def admin_handler(article):
..         if not authorize.is_role('admin'):
..             raise Unauthorized
..         pass

.. This authorization mechanism can be used in conjunction with ``User`` models using the ``UserRoleMixin``.


Database Mixins
---------------

Talk about what mixins are available and what they create

Content Authorization
+++++++++++++++++++++

* ``PermissionsMixin``: A mixin that enables authorization on the owner and group associated with a content item. The database columns included in this mixin are:

    - ``owner`` - The owner of the content. Defaults to the current_user when the object was created.
    - ``group`` - A single Group associated with the content.
    - ``permissions`` - JSON data encoding permissions for the content.

.. * ``ComplexPermissionsMixin``: A mixin that enables both user and multi-group authorization with a content item. The database columns included in this mixin are:

..     - ``owner`` - The owner of the content. Defaults to the current_user when the object was created.
..     - ``groups`` - Groups associated with the content.
..     - ``permissions`` - JSON data encoding permissions for the content.

* ``OwnerPermissionsMixin``: A mixin that enables only owner authorization with a content item. The database columns included in this mixin are:

    - ``owner`` - The owner of the content. Defaults to the current_user when the object was created.
    - ``permissions`` - JSON data encoding permissions for the content.

* ``GroupPermissionsMixin``: A mixin that enables only group authorization with a content item. The database columns included in this mixin are:

    - ``group`` - A single Group associated with the content.
    - ``permissions`` - JSON data encoding permissions for the content.

.. * ``GroupsPermissionsMixin``: A mixin that enables multi-group authorization with a content item. The database columns included in this mixin are:

..     - ``groups`` - A list of groups associated with the content.
..     - ``permissions`` - JSON data encoding permissions for the content.



Role/Group Authorization
++++++++++++++++++++++++

* ``RestrictionsMixin``: A mixin that enables restriction checking on ``Group`` or ``Role`` models associated with the ``current_user``. Database columns included in this mixin are:
    
    - ``restrictions``: JSON data encoding content restrictions associated with the group.

* ``AllowancesMixin``: A mixin that enables permission checking on ``Group`` or ``Role`` models associated with the ``current_user``. Database columns included in this mixin are:
    
    - ``allowances``: JSON data encoding content permissions associated with the group.


Jinja Support
-------------

In addition to using the ``authorize`` plugin for controlling rest-based data access, you can also use it in your Jinja templates. For example, if your request handler injects a set of ``Article`` instances into the template like so:

.. code-block:: python

    @app.route('/app/feed')
    def feed_view(self):
        articles = Article.query.limit(50).offset(0).all()
        return render_template('feed.html', articles=articles)


The ``feed.html`` template can contain the following Jinja expressions for conditionally rendering authorized content:

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

            <!-- add edit button -->
            {% if authorize.update(article) %}
                <button>Update Article</button>
            {% endif %}

            <!-- add delete button for administrators -->
            {% if authorize.in_group('admins') %}
                <button>Delete Article</button>
            {% endif %}

        {% endif %}
    {% endfor %}


The ``authorize`` decorator is automatically injected into the Jinja context, so developers can use any method available on the object.



Configuration
-------------

The following configuration values exist for Flask-Authorize.
Flask-Authorize loads these values from your main Flask config which can
be populated in various ways. Note that some of those cannot be modified
after the database engine was created so make sure to configure as early as
possible and to not modify them at runtime.

Configuration Keys
++++++++++++++++++

A list of configuration keys currently understood by the extension:

.. tabularcolumns:: |p{6.5cm}|p{10cm}|

===================================== =========================================
``AUTHORIZE_DEFAULT_PERMISSIONS``     Either a number that can be used as a
                                      permissions scheme (i.e. 764), or a dictionary
                                      like the following:

                                      .. code-block:: python

                                           dict(
                                               user=['read', 'update', 'delete'],
                                               group=['read', 'update'],
                                               other=['read']
                                           )

``AUTHORIZE_DISABLE_JINJA``           Don't add the ``authorize`` plugin to Jinja context.
                                      This disables jinja support.

``AUTHORIZE_DEFAULT_ALLOWANCES``      Default allowances for any model instantiated
                                      with a ``AllowancesMixin``.

``AUTHORIZE_DEFAULT_RESTRICTIONS``    Default restrictions for any model instantiated
                                      with a ``RestrictionsMixin``.

``AUTHORIZE_MODEL_PARSER``            How to determine key names for authorization or
                                      restriction data structures. By default, sqlalchemy
                                      table names will be used. The schemes for parsing
                                      keys are as follows:

                                        * table - Determine keys from sqlalchemy
                                          table names
                                        * class - Determine keys from sqlalchemy
                                          class names
                                        * lower - Determine keys from translating
                                          sqlalchemy class names to lower case.
                                        * snake - Determine keys from translating
                                          sqlalchemy class names to snake_case.

``AUTHORIZE_IGNORE_PROPERTY``         Model property that can be set to automatically
                                      skip all allowances/restrictions checks. This is
                                      useful for speeding up the authorization checks, if
                                      you don't need allowances/restrictions checks on
                                      specific models.

``AUTHORIZE_ALLOW_ANONYMOUS_ACTIONS`` Whether or not to allow actions if the function
                                      for returning the current user returns None
===================================== =========================================


Other Customizations
++++++++++++++++++++

As detailed in the `Overview <./overview.html>`_ section of the documentation,
the plugin can be customized with specific triggers. The following detail
what can be customized:

* ``current_user`` - The current user to authorize actions for. By default,
                     this uses the ``current_user`` object from
                     `Flask-Login <https://flask-login.readthedocs.io/en/latest/>`_.
* ``exception`` - An exception class to raise when the authorize plugin object is
                  used as a decorator and the current user does not have authorization
                  to perform an action. By default, this uses the ``Unauthorized``
                  exception from ``werkzeug.exceptions``.


The code below details how you can override all of these configuration options:

.. code-block:: python

    from flask import Flask, g
    from flask_authorize import Authorize
    from werkzeug.exceptions import HTTPException

    def get_current_user():
        return g.user

    class MyUnauthorizedException(HTTPException):
        code = 405
        description = 'Unauthorized'

    app = Flask(__name__)
    authorize = Authorize(
        current_user=get_current_user
        exception=MyUnauthorizedException
    )


For even more in-depth information on the module and the tools it provides, see the `API <./api.html>`_ section of the documentation.


Usage with Factory Boy
----------------------

By default, common factory-pattern utilities used in testing frameworks will set unreferenced properties to ``None`` instead of using model defaults for a property. To avoid this and set permissions explicitly during testing, use the ``factory.LazyFunction`` decorator with the ``default_permissions`` function from this package for any ``permissions`` properties on content models. See the example below for additional context:

.. code-block:: python
    
    import factory

    from flask_authorize import default_permissions


    # defining user and article factories
    class UserFactory(factory.alchemy.SQLAlchemyModelFactory):

        id = factory.Sequence(lambda x: x + 1)
        name = factory.Faker('name')
        email = factory.Faker('email')
        password = factory.Faker('password')

        class Meta:
            model = User
            sqlalchemy_session = db.session


    class ArticleFactory(factory.alchemy.SQLAlchemyModelFactory):

        id = factory.Sequence(lambda x: x + 1)
        name = factory.Faker('name')
        body = factory.Faker('paragraph')
        tags = factory.Faker('words')
        owner = factory.LazyFunction(UserFactory)
        permissions = factory.LazyFunction(default_permissions)

        class Meta:
            model = Article
            sqlalchemy_session = db.session


    # using factories to create models
    user = UserFactory.create()
    ArticleFactory.create(owner=user)



Code Structure and Clarity
--------------------------

When used in conjunction with `Flask-Occam <https://github.com/bprinty/Flask-Occam>`_, this plugin enables a very simple and understandable approach to API development. Here is an example of using the authorize decorators in that context:


.. code-block:: python

    @app.route('/items')
    class Items(object):

        def get(self):
            """
            GET /items

            Query for existing item in application database.

            Parameters:
                limit (str): (optional) Return limit for query.
                offset (str): (optional) Offset for querying results.

            Response:
                List of item objects. See GET /items/:id for
                information on return payloads.

            Status:
                Success: 200 Created
                Missing: 404 Not Found
            """
            items = list(filter(authorize.read, Item.all()))
            return [x.json() for x in items], 200

        @authorize.create(Item)
        @validate(name=str)
        @transactional
        def post(self):
            """
            POST /items

            Query for existing item in application database.

            Arguments:
                id (int): Identifier for item.

            Parameters:
                name (str): Name for item

            Response:
                id (int): Identifier for item.
                name (str): Item name.
                url (str): Item URL.

            Status:
                Success: 201 Created
                Missing: 404 Not Found
                Failure: 422 Invalid Request
            """
            item = Item.create(**request.json)
            return item.json(), 201


    @app.route('/items/<id(Item):item>')
    class SingleItem(object):
        
        @authorize.read
        def get(self, item):
            """
            GET /items/:id

            Query for existing item in application database.

            Arguments:
                id (int): Identifier for item.

            Response:
                id (int): Identifier for item.
                name (str): Item name.

            Status:
                Success: 200 OK
                Missing: 404 Not Found
            """
            return jsonify(id=item.id, name=item.name), 200

        @authorize.update
        @validate(
            name=optional(str),
            url=optional(validators.URL())
        )
        @transactional
        @log.info('Changed metadata for item {item.name}')
        def put(self, item):
            """
            PUT /items/:id

            Update existing item in application database.

            Arguments:
                id (int): Identifier for item.

            Parameters:
                name (str): (optional) Name for item 
                url (str): (optional) URL for item 

            Response:
                id (int): Identifier for item.
                name (str): Item name.
                url (str): Item url.

            Status:
                Success: 200 OK
                Missing: 404 Not Found
                Failure: 422 Invalid Request
            """
            item.update(**request.json)
            return item.json(), 200

        @authorize.delete
        @transactional
        def delete(self, item):
            """
            DELETE /items/:id

            Delete existing item in application database.

            Arguments:
                id (int): Identifier for item.

            Status:
                Success: 204 No Content
                Missing: 404 Not Found
            """
            item.delete()
            return jsonify(msg='Deleted item'), 204


For more information on the ``Flask-Occam`` module, see the `documentation <https://Flask-Occam.readthedocs.io>`_.
