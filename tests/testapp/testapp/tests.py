# -*- coding: utf-8 -*-

from __future__ import absolute_import

import pytest

import nplusone.ext.django  # noqa
from tests.utils import calls  # noqa
pytest.yield_fixture(calls)

from . import models


@pytest.fixture
def objects():
    user = models.User.objects.create()
    address = models.Address.objects.create(user=user)
    hobby = models.Hobby.objects.create()
    user.hobbies.add(hobby)
    return user, address


@pytest.mark.django_db
class TestManyToOne:

    def test_many_to_one(self, objects, calls):
        address = models.Address.objects.first()
        address.user
        assert len(calls) == 1
        assert calls[0] == (models.Address, 'user')

    def test_many_to_one_eager(self, objects, calls):
        address = models.Address.objects.select_related('user').first()
        address.user
        assert len(calls) == 0

    def test_many_to_one_reverse(self, objects, calls):
        user = models.User.objects.first()
        user.addresses.first()
        assert len(calls) == 1
        assert calls[0] == (models.User, 'addresses')


@pytest.mark.django_db
class TestManyToMany:

    def test_many_to_many(self, objects, calls):
        users = models.User.objects.all()
        list(users[0].hobbies.all())
        assert len(calls) == 1
        assert calls[0] == (models.User, 'hobbies')

    def test_many_to_many_eager(self, objects, calls):
        users = models.User.objects.all().prefetch_related('hobbies')
        users[0].hobbies.all()
        assert len(calls) == 0

    def test_many_to_many_reverse(self, objects, calls):
        hobbies = models.Hobby.objects.all()
        list(hobbies[0].users.all())
        assert len(calls) == 1
        assert calls[0] == (models.Hobby, 'users')
