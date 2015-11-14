# -*- coding: utf-8 -*-

import mock
import flask
import pytest
import webtest
import sqlalchemy as sa
from flask.ext.sqlalchemy import SQLAlchemy

from nplusone.core import notifiers
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

    @app.route('/eager_join_unused/')
    def eager_join_unused():
        user = models.User.query.options(sa.orm.joinedload('hobbies')).first()
        return str(user)

    @app.route('/eager_subquery_unused/')
    def eager_subquery_unused():
        user = models.User.query.options(sa.orm.subqueryload('hobbies')).first()
        return str(user)


@pytest.fixture
def client(app, routes, wrapper):
    return webtest.TestApp(app)


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
        res = client.get('/many_to_many/', expect_errors=True)
        assert res.status_code == 500
