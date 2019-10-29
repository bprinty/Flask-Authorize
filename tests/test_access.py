# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
from flask import g

from .fixtures import ArticleFactory, authorize


# tests
# -----
class TestAllowances(object):

    def test_allowances(self, client, allowed, unallowed):
        return


class TestRestrictions(object):

    def test_restrictions(self, client, restricted, unrestricted):
        return


class TestCredentials(object):

    def test_in_group(self, client, admin, reader, editor):
        article = ArticleFactory.create(
            name='Closed Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('000')

        g.user = reader
        assert authorize.in_group('readers')(article)
        assert not authorize.in_group('editors')(article)

        g.user = editor
        assert authorize.in_group('editors')(article)
        assert not authorize.in_group('readers')(article)
        return

    def test_has_role(self, client, reader, editor):
        article = ArticleFactory.create(
            name='Closed Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('000')

        g.user = reader
        assert authorize.has_role('readers')(article)
        assert not authorize.has_role('editors')(article)

        g.user = editor
        assert authorize.in_group('editors')(article)
        assert not authorize.in_group('readers')(article)
        return
