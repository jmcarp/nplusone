# -*- coding: utf-8 -*-

import sqlalchemy as sa


class Bunch(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def make_models(Base):

    users_hobbies = sa.Table('users_hobbies', Base.metadata,
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id')),
        sa.Column('hobby_id', sa.Integer, sa.ForeignKey('hobby.id')),
    )

    class User(Base):
        __tablename__ = 'user'
        id = sa.Column('user_id', sa.Integer, primary_key=True)
        addresses = sa.orm.relationship('Address', backref='user')
        hobbies = sa.orm.relationship('Hobby', secondary=users_hobbies, backref='users')

    class Address(Base):
        __tablename__ = 'address'
        id = sa.Column(sa.Integer, primary_key=True)
        user_id = sa.Column(sa.Integer, sa.ForeignKey('user.user_id'))

    class Hobby(Base):
        __tablename__ = 'hobby'
        id = sa.Column(sa.Integer, primary_key=True)

    return Bunch(
        User=User,
        Address=Address,
        Hobby=Hobby,
    )
