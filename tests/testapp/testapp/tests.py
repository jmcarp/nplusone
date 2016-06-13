# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import pytest

from django.conf import settings
from django_webtest import DjangoTestApp

from nplusone.ext.django.patch import setup_state

from . import models


@pytest.fixture(scope='module', autouse=True)
def setup():
    setup_state()


@pytest.fixture
def client():
    return DjangoTestApp()


@pytest.fixture
def objects():
    user = models.User.objects.create()
    user2 = models.User.objects.create()
    pet = models.Pet.objects.create(user=user)
    pet2 = models.Pet.objects.create(user=user2)
    allergy = models.Allergy.objects.create()
    allergy.pets.add(pet)
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
        assert call.objects == (models.Occupation, 'Occupation:1', 'user')
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
        assert call.objects == (models.User, 'User:1', 'occupation')
        assert 'user.occupation' in ''.join(call.frame[4])


@pytest.mark.django_db
class TestManyToOne:

    def test_many_to_one(self, objects, calls):
        address = models.Address.objects.first()
        address.user
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Address, 'Address:1', 'user')
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
        assert call.objects == (models.User, 'User:1', 'addresses')
        assert 'user.addresses' in ''.join(call.frame[4])

    def test_many_to_one_reverse_no_related_name(self, objects, calls):
        user = models.User.objects.first()
        user.pet_set.first()
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'User:1', 'pet_set')
        assert 'user.pet_set' in ''.join(call.frame[4])


@pytest.mark.django_db
class TestManyToMany:

    def test_many_to_many(self, objects, calls):
        users = models.User.objects.all()
        list(users[0].hobbies.all())
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'User:1', 'hobbies')
        assert 'users[0].hobbies' in ''.join(call.frame[4])

    def test_many_to_many_prefetch(self, objects, calls):
        users = models.User.objects.all().prefetch_related('hobbies')
        list(users[0].hobbies.all())
        assert len(calls) == 0

    def test_many_to_many_reverse(self, objects, calls):
        hobbies = models.Hobby.objects.all()
        list(hobbies[0].users.all())
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Hobby, 'Hobby:1', 'users')
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

    def test_one_to_one_first(self, objects, client, logger):
        client.get('/one_to_one_first/')
        assert not logger.log.called

    def test_one_to_many(self, objects, client, logger):
        client.get('/one_to_many/')
        assert not logger.log.called

    def test_many_to_many(self, objects, client, logger):
        client.get('/many_to_many/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_many_to_many_get(self, objects, client, logger):
        client.get('/many_to_many_get/')
        assert len(logger.log.call_args_list) == 0

    def test_many_to_many_reverse_no_related_name(self, objects, calls):
        pet = models.Pet.objects.first()
        pet.allergy_set.first()
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Pet, 'Pet:1', 'allergy_set')
        assert 'pet.allergy_set' in ''.join(call.frame[4])

    def test_prefetch_one_to_one(self, objects, client, logger):
        client.get('/prefetch_one_to_one/')
        assert not logger.log.called

    def test_prefetch_one_to_one_unused(self, objects, client, logger):
        client.get('/prefetch_one_to_one_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.occupation' in args[1]

    def test_prefetch_many_to_many(self, objects, client, logger):
        client.get('/prefetch_many_to_many/')
        assert not logger.log.called

    def test_prefetch_many_to_many_impossible(self, objects, client, logger):
        client.get('/prefetch_many_to_many_impossible/')
        assert not logger.log.called

    def test_prefetch_many_to_many_impossible_one(self, objects, client, logger):
        client.get('/prefetch_many_to_many_impossible_one/')
        assert not logger.log.called

    def test_prefetch_many_to_many_render(self, objects, client, logger):
        client.get('/prefetch_many_to_many_render/')
        assert not logger.log.called

    def test_prefetch_many_to_many_empty(self, objects, client, logger):
        models.User.objects.all().delete()
        client.get('/prefetch_many_to_many/')
        assert not logger.log.called

    def test_prefetch_many_to_many_render_empty(self, objects, client, logger):
        models.User.objects.all().delete()
        client.get('/prefetch_many_to_many_render/')
        assert not logger.log.called

    def test_prefetch_many_to_many_unused(self, objects, client, logger):
        client.get('/prefetch_many_to_many_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_prefetch_many_to_many_single(self, objects, client, logger):
        client.get('/prefetch_many_to_many_single/')
        assert not logger.log.called

    def test_prefetch_many_to_many_no_related_name(self, objects, client, logger):
        client.get('/prefetch_many_to_many_no_related/')
        assert not logger.log.called

    def test_select_one_to_one(self, objects, client, logger):
        client.get('/select_one_to_one/')
        assert not logger.log.called

    def test_select_one_to_one_unused(self, objects, client, logger):
        client.get('/select_one_to_one_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.occupation' in args[1]

    def test_select_many_to_one(self, objects, client, logger):
        client.get('/select_many_to_one/')
        assert not logger.log.called

    def test_select_many_to_one_empty(self, objects, client, logger):
        models.Pet.objects.all().delete()
        client.get('/select_many_to_one/')
        assert not logger.log.called

    def test_select_many_to_one_unused(self, objects, client, logger):
        client.get('/select_many_to_one_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'Pet.user' in args[1]

    def test_prefetch_nested(self, objects, client, logger):
        client.get('/prefetch_nested/')
        assert not logger.log.called

    def test_prefetch_nested_unused(self, objects, client, logger):
        client.get('/prefetch_nested_unused/')
        assert len(logger.log.call_args_list) == 2
        calls = [call[0] for call in logger.log.call_args_list]
        assert any('Pet.user' in call[1] for call in calls)
        assert any('User.occupation' in call[1] for call in calls)

    def test_select_nested(self, objects, client, logger):
        client.get('/select_nested/')
        assert not logger.log.called

    def test_select_nested_unused(self, objects, client, logger):
        client.get('/select_nested_unused/')
        assert len(logger.log.call_args_list) == 2
        calls = [call[0] for call in logger.log.call_args_list]
        assert any('Pet.user' in call[1] for call in calls)
        assert any('User.occupation' in call[1] for call in calls)

    def test_many_to_many_whitelist(self, objects, client, logger):
        settings.NPLUSONE_WHITELIST = [{'model': 'testapp.User'}]
        client.get('/many_to_many/')
        assert not logger.log.called


@pytest.mark.django_db
def test_values(objects, lazy_listener):
    list(models.User.objects.values('id'))
