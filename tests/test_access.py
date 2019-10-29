# -*- coding: utf-8 -*-
#
# Testing for role- and group-based access control.
#
# ------------------------------------------------


# imports
# -------
from .fixtures import ArticleFactory


# tests
# -----
class TestAllowances(object):

    def test_role_allowances(self, client, users):
        return

    def test_group_allowances(self, client, users):
        return


class TestRestrictions(object):

    def test_role_restrictions(self, client, users):
        return

    def test_group_restrictions(self, client, users):
        return


class TestCredentials(object):

    def test_in_group(self, client, users):
        return

    def test_has_role(self, client, users):
        return
