# -*- coding: utf-8 -*-

import mock
import flask
import pytest
import sqlalchemy as sa
from flask.ext.sqlalchemy import SQLAlchemy

import nplusone.ext.sqlalchemy  # noqa
from nplusone.ext.flask_sqlalchemy import NPlusOne

from tests import utils


@pytest.fixture
def db():
    return SQLAlchemy()


@pytest.fixture
def models(db):
    return utils.make_models(db.Model)


@pytest.fixture()
def objects(db, app, models):
    hobby = models.Hobby()
    address = models.Address()
    user = models.User(addresses=[address], hobbies=[hobby])
    db.session.add(user)
    db.session.commit()
    db.session.close()


@pytest.yield_fixture
def app(db, models):
    app = flask.Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    NPlusOne(app)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def wrapper(app):
    return NPlusOne(app)


@pytest.fixture
def routes(app, models):
    @app.route('/many_to_one/')
    def many_to_one():
        user = models.User.query.first()
        return str(user.addresses)

    @app.route('/many_to_many/')
    def many_to_many():
        user = models.User.query.first()
        return str(user.hobbies)

    @app.route('/eager/')
    def eager():
        user = models.User.query.options(sa.orm.subqueryload('hobbies')).first()
        return str(user.hobbies)


@pytest.yield_fixture
def client(app, routes):
    with app.test_client() as client:
        yield client


@pytest.fixture
def logger(wrapper, monkeypatch):
    mock_logger = mock.Mock()
    monkeypatch.setattr(wrapper, 'logger', mock_logger)
    return mock_logger


class TestNPlusOne:

    def test_many_to_one(self, objects, client, logger):
        client.get('/many_to_one/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.addresses' in args[1]

    def test_many_to_many(self, objects, client, logger):
        client.get('/many_to_many/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_eager(self, objects, client, logger):
        client.get('/eager/')
        assert not logger.log.called
