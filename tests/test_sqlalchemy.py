# -*- coding: utf-8 -*-

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

import nplusone.ext.sqlalchemy  # noqa
from tests.utils import calls  # noqa
pytest.yield_fixture(calls)


Base = declarative_base()


users_hobbies = sa.Table('users_hobbies', Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
    sa.Column('hobby_id', sa.Integer, sa.ForeignKey('hobby.id')),
)


class User(Base):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key=True)
    addresses = sa.orm.relationship('Address', backref='user')
    hobbies = sa.orm.relationship('Hobby', secondary=users_hobbies, backref='users')


class Address(Base):
    __tablename__ = 'address'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))


class Hobby(Base):
    __tablename__ = 'hobby'
    id = sa.Column(sa.Integer, primary_key=True)


@pytest.fixture()
def session():
    engine = sa.create_engine('sqlite:///:memory:')
    Session = sa.orm.sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return Session()


@pytest.fixture()
def objects(session):
    hobby = Hobby()
    address = Address()
    user = User(addresses=[address], hobbies=[hobby])
    session.add(user)
    session.commit()
    session.close()


class TestManyToOne:

    def test_many_to_one(self, session, objects, calls):
        user = session.query(User).first()
        user.addresses
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (User, 'addresses')
        assert 'user.addresses' in ''.join(call.frame[4])

    def test_many_to_one_subquery(self, session, objects, calls):
        user = session.query(User).options(sa.orm.subqueryload('addresses')).first()
        user.addresses
        assert len(calls) == 0

    def test_many_to_one_joined(self, session, objects, calls):
        user = session.query(User).options(sa.orm.joinedload('addresses')).first()
        user.addresses
        assert len(calls) == 0

    def test_many_to_one_reverse(self, session, objects, calls):
        address = session.query(Address).first()
        address.user
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (Address, 'user')
        assert 'address.user' in ''.join(call.frame[4])

    def test_many_to_one_reverse_subquery(self, session, objects, calls):
        address = session.query(Address).options(sa.orm.subqueryload('user')).first()
        address.user
        assert len(calls) == 0

    def test_many_to_one_reverse_joined(self, session, objects, calls):
        address = session.query(Address).options(sa.orm.joinedload('user')).first()
        address.user
        assert len(calls) == 0


class TestManyToMany:

    def test_many_to_many(self, session, objects, calls):
        user = session.query(User).first()
        user.hobbies
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (User, 'hobbies')
        assert 'user.hobbies' in ''.join(call.frame[4])

    def test_many_to_many_subquery(self, session, objects, calls):
        user = session.query(User).options(sa.orm.subqueryload('hobbies')).first()
        user.hobbies
        assert len(calls) == 0

    def test_many_to_many_joined(self, session, objects, calls):
        user = session.query(User).options(sa.orm.joinedload('hobbies')).first()
        user.hobbies
        assert len(calls) == 0

    def test_many_to_many_reverse(self, session, objects, calls):
        hobby = session.query(Hobby).first()
        hobby.users
        assert len(calls) == 1
        call = calls[0]
        assert call.objects == (Hobby, 'users')
        assert 'hobby.users' in ''.join(call.frame[4])

    def test_many_to_many_reverse_subquery(self, session, objects, calls):
        hobby = session.query(Hobby).options(sa.orm.subqueryload('users')).first()
        hobby.users
        assert len(calls) == 0

    def test_many_to_many_reverse_joined(self, session, objects, calls):
        hobby = session.query(Hobby).options(sa.orm.joinedload('users')).first()
        hobby.users
        assert len(calls) == 0
