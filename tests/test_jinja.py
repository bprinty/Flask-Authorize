# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
from flask import g

from .fixtures import ArticleFactory


# jinja
# -----
class TestJinja(object):

    def test_rendering(self, client, reader, editor, restricted, admin):
        g.user = None
        ArticleFactory.create(
            name='Jinja Article',
            owner=editor,
            group=editor.groups[0]
        )

        # no content shown
        g.user = restricted
        response = client.get('/feed')
        assert response.status_code == 200
        assert 'Create Article' not in str(response.data)
        assert 'Jinja Article' not in str(response.data)

        # content shown
        g.user = reader
        response = client.get('/feed')
        assert response.status_code == 200
        assert 'Create Article' in str(response.data)
        assert 'Update Article' not in str(response.data)
        assert 'Jinja Article' in str(response.data)
        assert 'Delete Article' not in str(response.data)

        # delete button shown
        g.user = admin
        response = client.get('/feed')
        assert response.status_code == 200
        assert 'Create Article' in str(response.data)
        assert 'Update Article' not in str(response.data)
        assert 'Jinja Article' in str(response.data)
        assert 'Delete Article' in str(response.data)
        return
