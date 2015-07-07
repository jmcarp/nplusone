# -*- coding: utf-8 -*-

import pytest
import peewee as pw

try:
    from playhouse.fields import ManyToManyField
except ImportError:
    from playhouse.shortcuts import ManyToManyField

from nplusone.core import signals
import nplusone.ext.peewee  # noqa

from tests.utils import calls, Bunch  # noqa
pytest.yield_fixture(calls)


@pytest.fixture
def db():
    return pw.SqliteDatabase(':memory:')


@pytest.fixture
def Base(db):
    class Base(pw.Model):
        class Meta:
            database = db
    return Base


@pytest.fixture
def models(Base):

    class Hobby(Base):
        pass

    class User(Base):
        hobbies = ManyToManyField(Hobby, related_name='users')

    class Address(Base):
        user = pw.ForeignKeyField(User, related_name='addresses')

    return Bunch(
        Hobby=Hobby,
        User=User,
        Address=Address,
    )


@pytest.yield_fixture
def session(db, models):
    db.create_tables(
        [
            models.User,
            models.Address,
            models.Hobby,
            models.User.hobbies.get_through_model()
        ],
        safe=True,
    )
    with db.atomic() as transaction:
        yield transaction


@pytest.fixture()
def objects(models, session):
    user = models.User.create(id=1)
    hobby = models.Hobby.create(id=1)
    hobby.users.add(user)
    address = models.Address.create(id=1, user=user)
    return Bunch(
        user=user,
        hobby=hobby,
        address=address,
    )


class TestManyToOne:

    def test_many_to_one(self, models, session, objects, calls):
        user = models.User.select().first()
        user.addresses
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'addresses')
        assert 'user.addresses' in ''.join(call.frame[4])

    def test_many_to_one_ignore(self, models, session, objects, calls):
        user = models.User.select().first()
        with signals.ignore(signals.lazy_load):
            user.addresses
        assert len(calls) == 0

    def test_many_to_one_aggregate(self, models, session, objects, calls):
        user = models.User.select(
            models.User,
            models.Address,
        ).join(
            models.Address
        ).aggregate_rows().first()
        user.addresses
        assert len(calls) == 0

    def test_many_to_one_reverse(self, models, session, objects, calls):
        address = models.Address.select().first()
        address.user
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Address, 'user')
        assert 'address.user' in ''.join(call.frame[4])

    def test_many_to_one_reverse_join(self, models, session, objects, calls):
        address = models.Address.select(
            models.Address,
            models.User,
        ).join(
            models.User
        ).first()
        address.user
        assert len(calls) == 0

    def test_many_to_one_reverse_prefetch(self, models, session, objects, calls):
        addresses = models.Address.select()
        users = models.User.select()
        address = pw.prefetch(addresses, users).first()
        address.user
        assert len(calls) == 0


class TestManyToMany:

    def test_many_to_many(self, models, session, objects, calls):
        user = models.User.select().first()
        list(user.hobbies)
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'hobbies')
        assert 'user.hobbies' in ''.join(call.frame[4])

    def test_many_to_many_reverse(self, models, session, objects, calls):
        hobby = models.Hobby.select().first()
        list(hobby.users)
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Hobby, 'users')
        assert 'hobby.users' in ''.join(call.frame[4])
