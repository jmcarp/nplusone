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
        user = session.query(models.User).first()
        user.addresses
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'addresses')
        assert 'user.addresses' in ''.join(call.frame[4])

    def test_many_to_one_ignore(self, session, objects, calls):
        user = session.query(models.User).first()
        with signals.ignore():
            user.addresses
        assert len(calls) == 0

    def test_many_to_one_subquery(self, session, objects, calls):
        user = session.query(
            models.User
        ).options(
            sa.orm.subqueryload('addresses')
        ).first()
        user.addresses
        assert len(calls) == 0

    def test_many_to_one_joined(self, session, objects, calls):
        user = session.query(models.User).options(sa.orm.joinedload('addresses')).first()
        user.addresses
        assert len(calls) == 0

    def test_many_to_one_reverse(self, session, objects, calls):
        address = session.query(models.Address).first()
        address.user
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Address, 'user')
        assert 'address.user' in ''.join(call.frame[4])

    def test_many_to_one_reverse_subquery(self, session, objects, calls):
        address = session.query(
            models.Address
        ).options(
            sa.orm.subqueryload('user')
        ).first()
        address.user
        assert len(calls) == 0

    def test_many_to_one_reverse_joined(self, session, objects, calls):
        address = session.query(models.Address).options(sa.orm.joinedload('user')).first()
        address.user
        assert len(calls) == 0


class TestManyToMany:

    def test_many_to_many(self, session, objects, calls):
        user = session.query(models.User).first()
        user.hobbies
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.User, 'hobbies')
        assert 'user.hobbies' in ''.join(call.frame[4])

    def test_many_to_many_subquery(self, session, objects, calls):
        user = session.query(models.User).options(sa.orm.subqueryload('hobbies')).first()
        user.hobbies
        assert len(calls) == 0

    def test_many_to_many_joined(self, session, objects, calls):
        user = session.query(models.User).options(sa.orm.joinedload('hobbies')).first()
        user.hobbies
        assert len(calls) == 0

    def test_many_to_many_reverse(self, session, objects, calls):
        hobby = session.query(models.Hobby).first()
        hobby.users
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (models.Hobby, 'users')
        assert 'hobby.users' in ''.join(call.frame[4])

    def test_many_to_many_reverse_subquery(self, session, objects, calls):
        hobby = session.query(models.Hobby).options(sa.orm.subqueryload('users')).first()
        hobby.users
        assert len(calls) == 0

    def test_many_to_many_reverse_joined(self, session, objects, calls):
        hobby = session.query(models.Hobby).options(sa.orm.joinedload('users')).first()
        hobby.users
        assert len(calls) == 0
