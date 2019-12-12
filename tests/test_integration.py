# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
import pytest
from flask import g
from werkzeug.exceptions import Unauthorized
from sqlalchemy import and_, or_

from .fixtures import authorize, Article, ArticleFactory


# authorizers
# -----------
@authorize.read
@authorize.create(Article)
@authorize.in_group('admins')
def in_group_or_read_and_create(article):
    pass


@authorize.read
@authorize.has_role('admins')
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
            items=['create', 'delete', 'read', 'update'],
        )

        from flask_authorize import default_restrictions
        assert default_restrictions() == dict(
            articles=[],
            items=[]
        )
        return


class TestIntegration(object):

    def test_in_group_or_read_and_create(self, client, reader, editor, admin, anonymous):
        g.user = None
        article = ArticleFactory.create(
            name='Complex Article 1',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('770')

        # no errors
        g.user = reader
        in_group_or_read_and_create(article)

        g.user = editor
        in_group_or_read_and_create(article)

        g.user = admin
        in_group_or_read_and_create(article)

        # errors
        g.user = anonymous
        with pytest.raises(Unauthorized):
            in_group_or_read_and_create(article)
        return

    def test_has_role_or_read(self, client, reader, editor, admin, anonymous):
        g.user = None
        article = ArticleFactory.create(
            name='Complex Article 2',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('700')

        # no errors
        g.user = reader
        has_role_or_read(article)

        g.user = admin
        has_role_or_read(article)

        # errors
        g.user = anonymous
        with pytest.raises(Unauthorized):
            has_role_or_read(article)
        return

    def test_multiple_permissions(self, client, reader, editor):
        g.user = reader
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


class TestQueryFilters(object):

    def test_query_filter_operations(self, reader, editor, anonymous):
        g.user = None
        article = ArticleFactory.create(
            name='Query Filter Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('770')

        # simple and_ filter
        g.user = reader
        articles = Article.query.filter(and_(
                Article.name == article.name,
                Article.authorized('read')
            )
        ).all()
        assert articles

        # complex and_/or_ operator
        g.user = editor
        articles = Article.query.filter(and_(
                Article.name == article.name,
                or_(
                    Article.authorized('read'),
                    Article.authorized('update')
                )
            )
        ).all()
        assert articles

        # and_ filter with negative query
        g.user = anonymous
        articles = Article.query.filter(and_(
                Article.name == article.name,
                Article.authorized('read')
            )
        ).all()
        assert not articles
        return
