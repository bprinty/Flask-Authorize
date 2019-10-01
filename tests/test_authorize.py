# -*- coding: utf-8 -*-
#
# Testing for Authorize decorator
#
# ------------------------------------------------


# imports
# -------
from .fixtures import ArticleFactory


# session
# -------
class TestOtherPermissions(object):

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
