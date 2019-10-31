# -*- coding: utf-8 -*-
#
# Testing for access control list authorization.
#
# ------------------------------------------------


# imports
# -------
from flask import g
from .fixtures import authorize, ArticleFactory


# session
# -------
class TestOtherPermissions(object):

    def test_other_delete(self, client, reader, editor):

        # other open read permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Delete Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('001')

        g.user = reader
        assert authorize.delete(article)

        # other closed read permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Delete Closed Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('770')

        g.user = reader
        assert not authorize.delete(article)
        return

    def test_other_read(self, client, reader, editor):

        # other open read permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Read Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('002')

        g.user = reader
        assert authorize.read(article)

        # other closed read permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Read Closed Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('660')

        g.user = reader
        assert not authorize.read(article)
        return

    def test_other_update(self, reader, editor):

        # other open update permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Write Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('004')

        g.user = reader
        assert authorize.update(article)

        # other closed update permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Write Closed Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('662')
        g.user = reader
        assert not authorize.update(article)
        return

    def test_other_custom(self, reader, editor):
        # other closed custom permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Custom Closed Article',
            owner=editor,
            group=editor.groups[0]
        )
        g.user = reader
        assert not authorize.custom(article)

        # other open custom permissions
        g.user = None
        article = ArticleFactory.create(
            name='Other Custom Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions(other=['custom'])

        g.user = reader
        assert authorize.custom(article)
        return


class TestOwnerPermissions(object):

    def test_owner_delete(self, client, reader, editor):
        g.user = reader

        # other open read permissions
        article = ArticleFactory.create(
            name='Owner Delete Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('100')
        assert authorize.delete(article)

        # other closed read permissions
        article = ArticleFactory.create(
            name='Owner Delete Closed Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('070')
        assert not authorize.delete(article)
        return

    def test_owner_read(self, client, reader, editor):
        g.user = reader

        # other open read permissions
        article = ArticleFactory.create(
            name='Owner Read Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('200')
        assert authorize.read(article)

        # other closed read permissions
        article = ArticleFactory.create(
            name='Owner Read Closed Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('170')
        assert not authorize.read(article)
        return

    def test_owner_update(self, reader, editor):
        g.user = reader

        # other open update permissions
        article = ArticleFactory.create(
            name='Owner Write Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('400')
        assert authorize.update(article)

        # other closed update permissions
        article = ArticleFactory.create(
            name='Owner Write Closed Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('270')
        assert not authorize.update(article)
        return

    def test_owner_custom(self, reader, editor):
        g.user = reader

        # other closed update permissions
        article = ArticleFactory.create(
            name='Owner Custom Closed Article',
            owner=reader,
            group=editor.groups[0]
        )
        assert not authorize.custom(article)

        # other open update permissions
        article = ArticleFactory.create(
            name='Owner Custom Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions(owner=['custom'])
        assert authorize.custom(article)
        return


class TestGroupPermissions(object):

    def test_group_delete(self, client, reader, editor):
        g.user = editor

        # other open read permissions
        article = ArticleFactory.create(
            name='Group Delete Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('010')
        assert authorize.delete(article)

        # other closed read permissions
        article = ArticleFactory.create(
            name='Group Delete Closed Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('700')
        assert not authorize.delete(article)
        return

    def test_group_read(self, client, reader, editor):
        g.user = editor

        # other open read permissions
        article = ArticleFactory.create(
            name='Group Read Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('020')
        assert authorize.read(article)

        # other closed read permissions
        article = ArticleFactory.create(
            name='Group Read Closed Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('710')
        assert not authorize.read(article)
        return

    def test_group_update(self, reader, editor):
        g.user = editor

        # other open update permissions
        article = ArticleFactory.create(
            name='Group Write Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('040')
        assert authorize.update(article)

        # other closed update permissions
        article = ArticleFactory.create(
            name='Group Write Closed Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions('720')
        assert not authorize.update(article)
        return

    def test_group_custom(self, reader, editor):
        g.user = editor

        # other closed update permissions
        article = ArticleFactory.create(
            name='Group Write Closed Article',
            owner=reader,
            group=editor.groups[0]
        )
        assert not authorize.custom(article)

        # other open update permissions
        article = ArticleFactory.create(
            name='Group Write Open Article',
            owner=reader,
            group=editor.groups[0]
        ).set_permissions(group=['custom'])
        assert authorize.custom(article)
        return
