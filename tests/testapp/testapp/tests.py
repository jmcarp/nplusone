# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import pytest

from django.conf import settings

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
        call = calls[0]
        assert call.objects == (models.Occupation, 'user')
        assert 'occupation.user' in ''.join(call.frame[4])

    def test_one_to_one_select(self, objects, calls):
        occupation = models.Occupation.objects.select_related('user').first()
        occupation.user
        assert len(calls) == 0

    def test_one_to_one_prefetch(self, objects, calls):
        occupation = models.Occupation.objects.prefetch_related('user').first()
        occupation.user
        assert len(calls) == 0

    def test_one_to_one_reverse(self, objects, calls):
        user = models.User.objects.first()
        user.occupation
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'occupation')
        assert 'user.occupation' in ''.join(call.frame[4])


@pytest.mark.django_db
class TestManyToOne:

    def test_many_to_one(self, objects, calls):
        address = models.Address.objects.first()
        address.user
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Address, 'user')
        assert 'address.user' in ''.join(call.frame[4])

    def test_many_to_one_select(self, objects, calls):
        address = list(models.Address.objects.select_related('user').all())
        address[0].user
        assert len(calls) == 0

    def test_many_to_one_prefetch(self, objects, calls):
        address = list(models.Address.objects.prefetch_related('user').all())
        address[0].user
        assert len(calls) == 0

    def test_many_to_one_reverse(self, objects, calls):
        user = models.User.objects.first()
        user.addresses.first()
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'addresses')
        assert 'user.addresses' in ''.join(call.frame[4])


@pytest.mark.django_db
class TestManyToMany:

    def test_many_to_many(self, objects, calls):
        users = models.User.objects.all()
        list(users[0].hobbies.all())
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'hobbies')
        assert 'users[0].hobbies' in ''.join(call.frame[4])

    def test_many_to_many_prefetch(self, objects, calls):
        users = models.User.objects.all().prefetch_related('hobbies')
        users[0].hobbies.all()
        assert len(calls) == 0

    def test_many_to_many_reverse(self, objects, calls):
        hobbies = models.Hobby.objects.all()
        list(hobbies[0].users.all())
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Hobby, 'users')
        assert 'hobbies[0].users' in ''.join(call.frame[4])

    def test_many_to_many_reverse_prefetch(self, objects, calls):
        hobbies = models.Hobby.objects.all().prefetch_related('users')
        list(hobbies[0].users.all())
        assert len(calls) == 0


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

    def test_eager_select(self, objects, client, logger):
        client.get('/eager_select/')
        assert not logger.log.called

    def test_eager_prefetch(self, objects, client, logger):
        client.get('/eager_prefetch/')
        assert not logger.log.called

    def test_eager_prefetch_item(self, objects, client, logger):
        client.get('/eager_prefetch_item/')
        assert not logger.log.called

    def test_eager_select_unused(self, objects, client, logger):
        client.get('/eager_select_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.occupation' in args[1]

    def test_eager_prefetch_scalar(self, objects, client, logger):
        client.get('/eager_prefetch_scalar/')
        assert not logger.log.called

    def test_eager_prefetch_scalar_unused(self, objects, client, logger):
        client.get('/eager_prefetch_scalar_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.occupation' in args[1]
