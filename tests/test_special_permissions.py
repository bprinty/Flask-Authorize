# -*- coding: utf-8 -*-
#
# Testing for access control list authorization.
#
# ------------------------------------------------


# imports
# -------
from sqlalchemy import and_
from flask import g

from .fixtures import authorize, Paper, PaperFactory, UserPaperAssociation


# helpers
# -------
def query(name, check):
    return Paper.query.filter(and_(
        Paper.name.contains(name),
        Paper.authorized(check)
    )).all()


# session
# -------
class TestSpecialPermissions(object):

    def test_special_read(self, client, special, editor):

        # create user and resource. resource is owned
        # by another user
        g.user = editor
        article = PaperFactory.create(
            name='Other Delete Open Article',
            owner=editor,
            group=editor.groups[0]
        ).set_permissions('660')

        # Set up association
        assoc = UserPaperAssociation(entity_id=g.user.id, resource_id=article.id, permissions=['read'])

        # give user read access
        assoc.paper = article
        special.special_papers.append(assoc)

        # switch the user
        g.user = special
        
        assert authorize.read(article)
        assert query(article.name, 'read')


    


