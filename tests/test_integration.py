# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
from flask import g
import pytest
from .fixtures import authorize, db, Article, ArticleFactory


# authorizers
# -----------
@authorize.read
@authorize.create(Article)
@authorize.in_group('test')
def in_group_or_read_or_create(article):
    pass


@authorize.read
@authorize.has_role('test')
def has_role_or_read(article):
    pass


# tests
# -----
class TestDefaults(object):

    def test_defaults(self, client):
        from flask_authorize import default_permissions
        assert default_permissions() == dict(
            owner=['delete', 'read', 'update'],
            group=['read', 'update'],
            other=['read']
        )

        from flask_authorize import default_allowances
        assert default_allowances() == dict(
            articles=['create', 'delete', 'read', 'update'],
        )

        from flask_authorize import default_restrictions
        assert default_restrictions() == dict(
            articles=[]
        )
        return


class TestIntegration(object):

    def test_in_group_or_read_or_create(self, client, reader, editor):
        article = ArticleFactory.create(
            name='Other Delete Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('001')

        g.user = reader
        return

    def test_has_role_or_read(self, client):
        return

    def test_multiple_permissions(self, client, reader, editor):
        allow = ArticleFactory.create(
            name='Multiple Permissions Open Article',
            owner=reader,
            group=reader.groups[0]
        ).set_permissions('777')
        deny = ArticleFactory.create(
            name='Multiple Permissions Closed Article',
            owner=reader,
            group=reader.groups[0]
        ).set_permissions('000')

        g.user = reader
        assert authorize.delete(allow)
        assert not authorize.delete(deny)
        assert not authorize.delete(allow, deny)

        assert authorize.read(allow)
        assert not authorize.read(deny)
        assert not authorize.read(allow, deny)

        assert authorize.update(allow)
        assert not authorize.update(deny)
        assert not authorize.update(allow, deny)
        return
