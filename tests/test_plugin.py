# -*- coding: utf-8 -*-
#
# Testing for decorator behavior of the authorize plugin.
#
# ------------------------------------------------


# imports
# -------
import pytest
from flask import g, jsonify
from werkzeug.exceptions import Unauthorized

from .fixtures import app, authorize
from .fixtures import UserFactory, GroupFactory, RoleFactory


# endpoints (same-named views, as with blueprints/class views)
# ------------------------------------------------------------
def make_first():
    def index():
        return jsonify(view='a')
    return index


def make_second():
    def index():
        return jsonify(view='b')
    return index


app.add_url_rule('/collision/a', 'collision_a', authorize.has_role('admins')(make_first()))
app.add_url_rule('/collision/b', 'collision_b', authorize.has_role('admins')(make_second()))


# same-named methods across classes (issue #60)
# ---------------------------------------------
class Invoice(object):

    @authorize.in_group('editors')
    def post(self, article):
        return


class Payment(object):

    @authorize.in_group('admins')
    def post(self, article):
        return


# tests
# -----
class TestNameCollision(object):

    def test_same_named_views_both_enforced(self, client, anonymous):
        # first view of shared name should be enforced
        response = client.get('/collision/a')
        assert response.status_code == 401

        # second same-named view should also be enforced (not raw function)
        response = client.get('/collision/b')
        assert response.status_code == 401
        return

    def test_same_named_methods_have_own_authorizer(self):
        # each wrapped method should carry its own authorizer
        assert Invoice().post.__authorize__.in_group == ['editors']
        assert Payment().post.__authorize__.in_group == ['admins']
        return

    def test_same_named_methods_both_enforced(self, client, editor, admin):
        from flask import g

        # editors can post invoices but not payments
        g.user = editor
        Invoice().post(None)
        with pytest.raises(Unauthorized):
            Payment().post(None)

        # admins can post payments but not invoices
        g.user = admin
        Payment().post(None)
        with pytest.raises(Unauthorized):
            Invoice().post(None)
        return


class TestRoleInheritance(object):

    def test_inherits_roles_via_group(self, client):
        role = RoleFactory.create(name='inherited-role')
        group = GroupFactory.create(name='inheritors', roles=[role])
        user = UserFactory.create(name='inheritor', groups=[group])

        g.user = user
        assert authorize.has_role('inherited-role')
        assert not authorize.has_role('other-role')
        return

    def test_direct_roles_still_work(self, client):
        role = RoleFactory.create(name='direct-role')
        user = UserFactory.create(name='director', roles=[role])

        g.user = user
        assert authorize.has_role('direct-role')
        assert not authorize.has_role('inherited-role')
        return

    def test_groups_without_roles_unaffected(self, client, editor):
        g.user = editor
        assert authorize.has_role('editors')
        assert not authorize.has_role('inherited-role')
        return

