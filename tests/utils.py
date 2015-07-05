# -*- coding: utf-8 -*-

import collections

import pytest
import sqlalchemy as sa

from nplusone.core import stack
from nplusone.core import signals


Call = collections.namedtuple('Call', ['objects', 'frame'])


@pytest.yield_fixture
def calls():
    calls = []
    def subscriber(sender, args=None, kwargs=None, context=None, parser=None):
        calls.append(
            Call(
                parser(args, kwargs, context),
                stack.get_caller(),
            )
        )
    signals.lazy_load.connect(subscriber, sender=signals.get_worker())
    yield calls


class Bunch(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def make_models(Base):

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

    return Bunch(
        User=User,
        Address=Address,
        Hobby=Hobby,
    )
