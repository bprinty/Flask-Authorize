
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


Moreover, there are several mechanisms for assigning permissions to users
of the application:

* Role-based access control via permissions or restrictions (RBACs).
* Group-based access control via permissions or restrictions.
* Access rights for existing content via owner/group(s) and permission scheme (ACLs).



.. Wikipedia provides a good description of the purpose of ACLS:

.. An access-control list (ACL), with respect to a computer file system, is a list of permissions attached to an object. An ACL specifies which users or system processes are granted access to objects, as well as what operations are allowed on given objects.[1] Each entry in a typical ACL specifies a subject and an operation. For instance, if a file object has an ACL that contains (Alice: read,write; Bob: read), this would give Alice permission to read and write the file and Bob to only read it.

However, there are many different schemes for providing access control, such as Role-based access control, access control lists, or custom schemes. This plugin provides a flexible set of tools to accommodate each of these schemes, where developers can simply use what their application requires.



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


Restrictions
------------

Both ``Role`` and ``Group`` models can have optional restrictions on specific operations:

.. code-block:: python

    # create user and associated role
    role = Role(
        name='reader',
        restrictions=dict(
            'articles': 'cud' # create, update, and delete restriction
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



Content Permissions
-------------------

In administrating content authorization, there are several different pieces

Permissions administration for this plugin was inspired by Filesystem ACLs in Linux, where content (files) are associated with three things: an owner, a group, and a set of permissions.

.. code-block:: python

    # via numeric scheme
    class Article(db.Model, PermissionsMixin):
        __permissions__ = '764' # owner (read, write, delete)
                                # group (read, write)
                                # other (read)


    # with explicit syntax
    class Article(db.Model, PermissionsMixin):
        __permissions__ = dict(
            owner='rwd',
            group='rw',
            other='r'
        )


By default the settings value for ``AUTHORIZE_DEFAULT_PERMISSIONS`` will be used.



Logical Flow
------------

Creating New Content
++++++++++++++++++++

If the content has


Viewing/Editing Existing Content
++++++++++++++++++++++++++++++++

If the content


What's actually necessary?
--------------------------

It really depends on how you want to structure your application, if your application requires only User or Other content restrictions.


Database Mixins
---------------

Talk about what mixins are available and what they create

``PermissionsMixin``: A mixin that can be added to models ...

``MultiGroupPermissionsMixin``: A mixin that can be added to models to enforce access control, where the entities check against are:
    
    * ``owner`` - The owner of the content.
    * ``groups`` - Groups associated with the content.


``RoleAuthMixin``: Equivalent to defining the following model:

.. code-block:: python

    test


``GroupAuthMixin``
``UserAuthMixin``


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
