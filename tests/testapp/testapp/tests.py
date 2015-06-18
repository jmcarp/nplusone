# -*- coding: utf-8 -*-

from __future__ import absolute_import

import pytest
from unittest import mock

from django.conf import settings

import nplusone.ext.django  # noqa
from tests.utils import calls  # noqa
pytest.yield_fixture(calls)

from . import models


@pytest.fixture
def objects():
    user = models.User.objects.create()
    occupation = models.Occupation.objects.create(user=user)
    address = models.Address.objects.create(user=user)
    hobby = models.Hobby.objects.create()
    user.hobbies.add(hobby)
    return locals()


@pytest.mark.django_db
class TestOneToOne:

    def test_one_to_one(self, objects, calls):
        occupation = models.Occupation.objects.first()
        occupation.user
        assert len(calls) == 1
        assert calls[0] == (models.Occupation, 'user')

    def test_one_to_one_eager(self, objects, calls):
        occupation = models.Occupation.objects.select_related('user').first()
        occupation.user
        assert len(calls) == 0

    def test_one_to_one_reverse(self, objects, calls):
        user = models.User.objects.first()
        user.occupation
        assert len(calls) == 1
        assert calls[0] == (models.User, 'occupation')


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


@pytest.fixture
def logger(monkeypatch):
    mock_logger = mock.Mock()
    monkeypatch.setattr(settings, 'NPLUSONE_LOGGER', mock_logger)
    return mock_logger


@pytest.mark.django_db
class TestIntegration:

    def test_one_to_one(self, objects, client, logger):
        client.get('/one_to_one/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'Occupation.user' in args[1]

    def test_many_to_many(self, objects, client, logger):
        client.get('/many_to_many/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_eager(self, objects, client, logger):
        client.get('/eager/')
        assert not logger.log.called
