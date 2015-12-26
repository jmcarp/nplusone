# -*- coding: utf-8 -*-

import mock
import flask
import pytest
import webtest
import sqlalchemy as sa
from flask.ext.sqlalchemy import SQLAlchemy

from nplusone.core import notifiers
from nplusone.core import exceptions
from nplusone.ext.flask_sqlalchemy import NPlusOne
from nplusone.ext.flask_sqlalchemy import setup_state

from tests import utils


@pytest.fixture(scope='module', autouse=True)
def setup():
    setup_state()


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


@pytest.fixture
def logger():
    return mock.Mock()


@pytest.yield_fixture
def app(db, models, logger):
    app = flask.Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['NPLUSONE_LOGGER'] = logger
    db.init_app(app)
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
        users = models.User.query.all()
        return str(users[0].addresses)

    @app.route('/many_to_one_first/')
    def many_to_one_first():
        user = models.User.query.first()
        return str(user.addresses)

    @app.route('/many_to_many/')
    def many_to_many():
        users = models.User.query.all()
        return str(users[0].hobbies)

    @app.route('/eager/')
    def eager():
        users = models.User.query.options(sa.orm.subqueryload('hobbies')).all()
        return str(users[0].hobbies)

    @app.route('/eager_join_unused/')
    def eager_join_unused():
        users = models.User.query.options(sa.orm.joinedload('hobbies')).all()
        return str(users[0])

    @app.route('/eager_subquery_unused/')
    def eager_subquery_unused():
        users = models.User.query.options(sa.orm.subqueryload('hobbies')).all()
        return str(users[0])


@pytest.fixture
def client(app, routes, wrapper):
    return webtest.TestApp(app)


class TestNPlusOne:

    def test_many_to_one(self, objects, client, logger):
        client.get('/many_to_one/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.addresses' in args[1]

    def test_many_to_one_first(self, objects, client, logger):
        client.get('/many_to_one_first/')
        assert not logger.log.called

    def test_many_to_many(self, objects, client, logger):
        client.get('/many_to_many/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_eager(self, objects, client, logger):
        client.get('/eager/')
        assert not logger.log.called

    def test_eager_join_unused(self, objects, client, logger):
        client.get('/eager_join_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_eager_subquery_unused(self, objects, client, logger):
        client.get('/eager_subquery_unused/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_many_to_many_raise(self, app, wrapper, objects, client, logger):
        app.config['NPLUSONE_RAISE'] = True
        wrapper.notifiers = notifiers.init(app.config)
        with pytest.raises(exceptions.NPlusOneError):
            client.get('/many_to_many/')
