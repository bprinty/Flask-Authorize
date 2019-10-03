
Usage
=====

The sections below detail how to fully use this module, along with
context for some of the design decisions made during development
of the plugin.



Access Control
--------------

Applications housing sensitive material are often required to restrict
certain types of access to both content and actions related to that
content. This means that developers of the application need the ability
to either permit or deny:

* Creation of new content.
* Read access to existing content.
* Updates to existing content.
* Deletion of existing content.
* Other customized specific actions on existing content.

Moreover, there are several mechanisms for assigning permissions to users
of the application:

* Role-based access control via permissions or restrictions (RBACs).
* Group-based access control via permissions or restrictions.
* Access rights for existing content via owner/group(s) and permission schemes (ACLs).

This package tries to accomodate each of these needs, providing a flexible set of tools to accommodate each of these schemes, where developers can simply use what their application requires.


.. Wikipedia provides a good description of the purpose of ACLS:


However, there are many different schemes for providing access control, such as Role-based access control, access control lists, or custom schemes. 



Users, Roles, Groups
--------------------

To understand the nuances of each model, let's go over the purpose of each.

* User: A user represents a singular entity that is interacting with the application. They can assume multiple roles or be part of multiple groups.

* Role: A role represents an identity that a user can take while performing certain actions in the application. Roles are typically associated with permissions or permission restrictions.

* Group: A group represents a collection of users. Groups can be associated with permissions or permission restrictions.


Let's use the analogy of a basketball team to make things more concrete. In this analogy, examples of each model are as follows:

* Users: MJ, Scottie Pippen, Dennis Rodman, Toni Kukoc, Steve Kerr, Robert Parish

* Roles: Shooting Guard, Small Forward, Power Forward, Point Guard

* Group: Bulls, Team Captains, Scorers, Role-Players


What's actually necessary?
--------------------------

It really depends on how you want to structure your application, if your application requires only User or Other content restrictions.


Configuring User/Role/Group Models
----------------------------------

In order for Flask-Authorize to be fully utilized for access management, the following are required:


Content Permissions
-------------------

Permissions administration for this plugin was inspired by Filesystem ACLs in Linux, where content (files) are associated with three things: an owner, a group, and a set of permissions. ...


By default the settings value for ``AUTHORIZE_DEFAULT_PERMISSIONS`` will be used.


Standard permissions for content:

.. code-block:: python

    class Article(db.Model, PermissionsMixin):
        __permissions__ = dict(
            user='rud', # read + update + delete permissions
            group='ru', # read + update permissions
            other='r',  # read permissions
        )


You can also assign permissions with a more explicit syntax:

.. code-block:: python

    class Article(db.Model, PermissionsMixin):
        __permissions__ = dict(
            owner=['read', 'update', 'delete'],
            group=['read', 'update'],
            other=['read']
        )


This more explicit syntax is designed to allow for more customized authorization schemes. For the `Article` example, to add a permission specific to `revoke`-ing an article, you can configure the permissions like so:

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


Restrictions
------------

In addition to authorizing permissions on created content, we can also add another layer 


Both ``Role`` and ``Group`` models configured with the ``RoleAuthMixin`` and ``GroupAuthMixin`` can have optional restrictions on specific operations:

.. code-block:: python

    # create user and associated role
    role = Role(
        name='reader',
        restrictions=dict(
            articles='cud'           # create, update, and delete restriction
            secret_articles='crud'   # create, read, update, and delete restriction
        )
    )
    user = User(name='User 1')
    user.roles = [role]
    db.session.add(role, user)
    db.session.commit()



With the users and roles configured above, you can enforce these permissions in api methods like so:


.. code-block:: python

    # via decoration
    @authorize.create(Article)
    def create_article(name):
        # will raise an Unauthorized error if the user
        # is not authorized to create articles
        pass

    @authorize.update
    def update_article(name):
        # will raise an Unauthorized error if the user
        # is not authorized to create articles
        pass

    @authorize.delete
    @authorize.role('admin')
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

If you want to explicitly allow access to each type of action (i.e. the inverse of **restrictions**), you can do so using the ``RoleAllowanceMixin`` and ``GroupAllowanceMixin`` mixin objects when defining your models. See the `Database Mixins`_ section below for more details on what each of the mixins provide.

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


Logical Flow
------------

Creating New Content
++++++++++++++++++++

If the content has


Viewing/Editing Existing Content
++++++++++++++++++++++++++++++++

If the content


Database Mixins
---------------

Talk about what mixins are available and what they create

``PermissionsMixin``: A mixin that can be added to models ...
``OwnerPermissionsMixin``
``GroupPermissionsMixin``
``MultiGroupPermissionsMixin``

``MultiGroupPermissionsMixin``: A mixin that can be added to models to enforce access control, where the entities check against are:
    
    * ``owner`` - The owner of the content.
    * ``groups`` - Groups associated with the content.


``RoleAuthMixin``: Equivalent to defining the following model:

.. code-block:: python

    test

``GroupRestrictionMixin``
``GroupPermissionMixin``
``RoleRestrictionMixin``
``RolePermissionMixin``


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

================================== =========================================
``AUTHORIZE_DEFAULT_PERMISSIONS``  Either a number that can be used as a
                                   permissions scheme (i.e. 764), or a dictionary
                                   like the following:

                                   .. code-block:: python

                                        dict(
                                            user='rud',  # read, update, delete
                                            group='ru',  # read, update
                                            other='r'    # read
                                        )
================================== =========================================


Other Customizations
++++++++++++++++++++

As detailed in the `Overview <./overview.html>`_ section of the documentation,
the plugin can be customized with specific triggers. The following detail
what can be customized:

* ``current_user`` - The current user to authorize actions for. By default,
                     this uses the ``current_user`` object from
                     `Flask-Login <https://flask-login.readthedocs.io/en/latest/>`_.
* ``exc`` - An exception class to raise when the authorize plugin object is
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
        exc=MyUnauthorizedException
    )



For even more in-depth information on the module and the tools it provides, see the `API <./api.html>`_ section of the documentation.
