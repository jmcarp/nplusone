# -*- coding: utf-8 -*-

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from nplusone.core import signals
import nplusone.ext.sqlalchemy  # noqa


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


def collect_calls():
    calls = []
    def subscriber(sender, args=None, kwargs=None, context=None, parser=None):
        calls.append(parser(args, kwargs, context))
    signals.lazy_load.connect(subscriber)
    return calls, subscriber


def test_one_to_many(session, objects):
    user = session.query(User).first()
    calls, subscriber = collect_calls()
    user.addresses
    assert len(calls) == 1
    assert calls[0] == (User, 'addresses')


def test_many_to_one(session, objects):
    address = session.query(Address).first()
    calls, subscriber = collect_calls()
    address.user
    assert len(calls) == 1
    assert calls[0] == (Address, 'user')


def test_many_to_many(session, objects):
    user = session.query(User).first()
    calls, subscriber = collect_calls()
    user.hobbies
    assert len(calls) == 1
    assert calls[0] == (User, 'hobbies')
