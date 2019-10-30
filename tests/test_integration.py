# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
from flask import g
import pytest
from .fixtures import authorize, Article, ArticleFactory


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
class TestIntegration(object):

    def test_in_group_or_read_or_create(self, client, reader, editor):
        article = ArticleFactory.create(
            name='Other Delete Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('001')

        g.user = reader
        return

    def test_has_role_or_read(self, client, users):
        return
