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
class TestPermissions(object):

    def test_other_read(self, client, users):
        g.user = None

        # other open read permissions
        article = ArticleFactory.create(
            name='Other Read Open Article',
            permissions='002',
            owner=users[1],
            group=users[1].groups[0]
        )
        print(users[1].name)
        print(article.name)
        assert authorize.read(article)

        # other closed read permissions
        article = ArticleFactory.create(
            name='Other Read Closed Article',
            permissions='660',
            owner=users[1],
            group=users[1].groups[0]
        )
        assert not authorize.read(article)
        return

    # def test_other_write(self, client, users):
    #     # other open read permissions
    #     article = ArticleFactory.create(
    #         name='Other Write Open Article',
    #         permissions='004',
    #         owner=users[1],
    #         group=users[1].groups[0]
    #     )
    #     headers = {}
    #     response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
    #     assert response.status_code == 200

    #     # other closed read permissions
    #     article = ArticleFactory.create(
    #         name='Other Write Closed Article',
    #         permissions='662',
    #         owner=users[1],
    #         group=users[1].groups[0]
    #     )
    #     headers = {}
    #     response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
    #     assert response.status_code == 401
    #     return

    # def test_user_read(self, client, users):
    #     # other open read permissions
    #     article = ArticleFactory.create(
    #         name='Read User Open Article',
    #         permissions='200',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[1].token}
    #     response = client.get('/articles/{}'.format(article.id), headers=headers)
    #     assert response.status_code == 200

    #     # other closed user read permissions
    #     article = ArticleFactory.create(
    #         name='Read User Closed Article',
    #         permissions='060',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[1].token}
    #     response = client.get('/articles/{}'.format(article.id), headers=headers)
    #     assert response.status_code == 401
    #     return

    # def test_user_write(self, client, users):
    #     # other open read permissions
    #     article = ArticleFactory.create(
    #         name='Write User Open Article',
    #         permissions='400',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[1].token}
    #     response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
    #     assert response.status_code == 200

    #     # other closed user read permissions
    #     article = ArticleFactory.create(
    #         name='Write User Closed Article',
    #         permissions='260',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[1].token}
    #     response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
    #     assert response.status_code == 401
    #     return

    # def test_group_read(self, client, users):
    #     # other group read permissions
    #     article = ArticleFactory.create(
    #         name='Read Group Open Article',
    #         permissions='020',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[0].token}
    #     response = client.get('/articles/{}'.format(article.id), headers=headers)
    #     assert response.status_code == 200

    #     # other closed group read permissions
    #     article = ArticleFactory.create(
    #         name='Read Group Closed Article',
    #         permissions='600',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[0].token}
    #     response = client.get('/articles/{}'.format(article.id), headers=headers)
    #     assert response.status_code == 401
    #     return

    # def test_group_write(self, client, users):
    #     # other group read permissions
    #     article = ArticleFactory.create(
    #         name='Write Group Open Article',
    #         permissions='040',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[0].token}
    #     response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
    #     assert response.status_code == 200

    #     # other closed group read permissions
    #     article = ArticleFactory.create(
    #         name='Write Group Closed Article',
    #         permissions='620',
    #         owner=users[1],
    #         group=users[0].groups[0]
    #     )
    #     headers = {'Authorization': 'Bearer ' + users[0].token}
    #     response = client.put('/articles/{}'.format(article.id), json=dict(name='test'), headers=headers)
    #     assert response.status_code == 401
    #     return
