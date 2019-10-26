# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
import pytest
from .fixtures import authorize, Article, ArticleFactory


# authorizers
# -----------
@authorize.read
@authorize.write(Article)
@authorize.in_group('test')
def in_group_or_read_write(article):
    pass


@authorize.read
@authorize.has_role('test')
def has_role_or_read(article):
    pass


# tests
# -----
class TestComplex(object):

    def test_in_group_or_read_write(self, client, users):
        return

    def test_has_role_or_read(self, client, users):
        return


class TestIntegration(object):

    def test_other_read(self, client, users):
        # other open read permissions
        article = ArticleFactory.create(
            name='Read Open Article',
            permissions='002',
            owner=users[1],
            group=users[1].groups[0]
        )
        headers = {}
        response = client.get('/articles/{}'.format(article.id), headers=headers)
        assert response.status_code == 200

        # other closed read permissions
        article = ArticleFactory.create(
            name='Read Closed Article',
            permissions='660',
            owner=users[1],
            group=users[1].groups[0]
        )
        headers = {}
        response = client.get('/articles/{}'.format(article.id), headers=headers)
        assert response.status_code == 401
        return

    def test_other_write(self, client, users):
        # other open read permissions
        article = ArticleFactory.create(
            name='Write Open Article',
            permissions='004',
            owner=users[1],
            group=users[1].groups[0]
        )
        headers = {}
        response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
        assert response.status_code == 200

        # other closed read permissions
        article = ArticleFactory.create(
            name='Write Closed Article',
            permissions='662',
            owner=users[1],
            group=users[1].groups[0]
        )
        headers = {}
        response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
        assert response.status_code == 401
        return

    def test_user_read(self, client, users):
        # other open read permissions
        article = ArticleFactory.create(
            name='Read User Open Article',
            permissions='200',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[1].token}
        response = client.get('/articles/{}'.format(article.id), headers=headers)
        assert response.status_code == 200

        # other closed user read permissions
        article = ArticleFactory.create(
            name='Read User Closed Article',
            permissions='060',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[1].token}
        response = client.get('/articles/{}'.format(article.id), headers=headers)
        assert response.status_code == 401
        return

    def test_user_write(self, client, users):
        # other open read permissions
        article = ArticleFactory.create(
            name='Write User Open Article',
            permissions='400',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[1].token}
        response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
        assert response.status_code == 200

        # other closed user read permissions
        article = ArticleFactory.create(
            name='Write User Closed Article',
            permissions='260',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[1].token}
        response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
        assert response.status_code == 401
        return

    def test_group_read(self, client, users):
        # other group read permissions
        article = ArticleFactory.create(
            name='Read Group Open Article',
            permissions='020',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[0].token}
        response = client.get('/articles/{}'.format(article.id), headers=headers)
        assert response.status_code == 200

        # other closed group read permissions
        article = ArticleFactory.create(
            name='Read Group Closed Article',
            permissions='600',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[0].token}
        response = client.get('/articles/{}'.format(article.id), headers=headers)
        assert response.status_code == 401
        return

    def test_group_write(self, client, users):
        # other group read permissions
        article = ArticleFactory.create(
            name='Write Group Open Article',
            permissions='040',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[0].token}
        response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
        assert response.status_code == 200

        # other closed group read permissions
        article = ArticleFactory.create(
            name='Write Group Closed Article',
            permissions='620',
            owner=users[1],
            group=users[0].groups[0]
        )
        headers = {'Authorization': 'Bearer ' + users[0].token}
        response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
        assert response.status_code == 401
        return