# -*- coding: utf-8 -*-

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from nplusone.core import signals
import nplusone.ext.sqlalchemy  # noqa

from tests import utils
from tests.utils import calls  # noqa
pytest.yield_fixture(calls)


Base = declarative_base()


models = utils.make_models(Base)


@pytest.fixture()
def session():
    engine = sa.create_engine('sqlite:///:memory:')
    Session = sa.orm.sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return Session()


@pytest.fixture()
def objects(session):
    hobby = models.Hobby()
    address = models.Address()
    user = models.User(addresses=[address], hobbies=[hobby])
    session.add(user)
    session.commit()
    session.close()


class TestManyToOne:

    def test_many_to_one(self, session, objects, calls):
        users = session.query(models.User).all()
        users[0].addresses
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'User:1', 'addresses')
        assert 'users[0].addresses' in ''.join(call.frame[4])

    def test_many_to_one_ignore(self, session, objects, calls):
        users = session.query(models.User).all()
        with signals.ignore(signals.lazy_load):
            users[0].addresses
        assert len(calls) == 0

    def test_many_to_one_subquery(self, session, objects, calls):
        users = session.query(
            models.User
        ).options(
            sa.orm.subqueryload('addresses')
        ).all()
        users[0].addresses
        assert len(calls) == 0

    def test_many_to_one_joined(self, session, objects, calls):
        users = session.query(models.User).options(sa.orm.joinedload('addresses')).all()
        users[0].addresses
        assert len(calls) == 0

    def test_many_to_one_reverse(self, session, objects, calls):
        addresses = session.query(models.Address).all()
        addresses[0].user
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Address, 'Address:1', 'user')
        assert 'addresses[0].user' in ''.join(call.frame[4])

    def test_many_to_one_reverse_subquery(self, session, objects, calls):
        addresses = session.query(
            models.Address
        ).options(
            sa.orm.subqueryload('user')
        ).all()
        addresses[0].user
        assert len(calls) == 0

    def test_many_to_one_reverse_joined(self, session, objects, calls):
        address = session.query(models.Address).options(sa.orm.joinedload('user')).first()
        address.user
        assert len(calls) == 0


class TestManyToMany:

    def test_many_to_many(self, session, objects, calls):
        users = session.query(models.User).all()
        users[0].hobbies
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'User:1', 'hobbies')
        assert 'users[0].hobbies' in ''.join(call.frame[4])

    def test_many_to_many_subquery(self, session, objects, calls):
        user = session.query(models.User).options(sa.orm.subqueryload('hobbies')).first()
        user.hobbies
        assert len(calls) == 0

    def test_many_to_many_joined(self, session, objects, calls):
        user = session.query(models.User).options(sa.orm.joinedload('hobbies')).first()
        user.hobbies
        assert len(calls) == 0

    def test_many_to_many_reverse(self, session, objects, calls):
        hobbies = session.query(models.Hobby).all()
        hobbies[0].users
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Hobby, 'Hobby:1', 'users')
        assert 'hobbies[0].users' in ''.join(call.frame[4])

    def test_many_to_many_reverse_subquery(self, session, objects, calls):
        hobby = session.query(models.Hobby).options(sa.orm.subqueryload('users')).first()
        hobby.users
        assert len(calls) == 0

    def test_many_to_many_reverse_joined(self, session, objects, calls):
        hobby = session.query(models.Hobby).options(sa.orm.joinedload('users')).first()
        hobby.users
        assert len(calls) == 0
