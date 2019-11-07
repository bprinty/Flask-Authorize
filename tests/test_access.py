# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
from flask import g

from .fixtures import Article, ArticleFactory, authorize


# tests
# -----
class TestAccessControl(object):

    def test_allowances(self, client, reader, allowed, unallowed):
        g.user = None
        article = ArticleFactory.create(
            name='Allowances Open Article',
            owner=reader,
            group=reader.groups[0]
        ).set_permissions('777')

        g.user = allowed
        assert authorize.read(article)
        assert authorize.create(Article)

        g.user = unallowed
        assert not authorize.read(article)
        assert not authorize.create(Article)
        return

    def test_restrictions(self, client, reader, restricted, unrestricted):
        g.user = None
        article = ArticleFactory.create(
            name='Restrictions Open Article',
            owner=reader,
            group=reader.groups[0]
        ).set_permissions('777')

        g.user = unrestricted
        assert authorize.read(article)
        assert authorize.create(Article)

        g.user = restricted
        assert not authorize.read(article)
        assert not authorize.create(Article)
        return


class TestCredentials(object):

    def test_in_group(self, client, admin, reader, editor):
        g.user = reader
        assert authorize.in_group('readers')
        assert not authorize.in_group('editors')

        g.user = editor
        assert authorize.in_group('editors')
        assert not authorize.in_group('readers')
        return

    def test_has_role(self, client, reader, editor):
        g.user = reader
        assert authorize.has_role('readers')
        assert not authorize.has_role('editors')

        g.user = editor
        assert authorize.in_group('editors')
        assert not authorize.in_group('readers')
        return
