# -*- coding: utf-8 -*-

import flask
import pytest
import blinker
import webtest
from flask_sqlalchemy import SQLAlchemy

from nplusone.core import signals
from nplusone.core import exceptions
from nplusone.ext.wsgi import NPlusOneMiddleware
import nplusone.ext.sqlalchemy  # noqa

from tests import utils


@pytest.fixture(scope='module', autouse=True)
def setup():
    signals.get_worker = lambda *a, **kw: blinker.ANY


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
def app(db, models):
    app = flask.Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def routes(app, models, wrapper):
    @app.route('/many_to_one/')
    def many_to_one():
        users = models.User.query.all()
        return str(users[0].addresses)

    @app.route('/many_to_one_one/')
    def many_to_one_one():
        user = models.User.query.filter_by(id=1).one()
        return str(user.addresses)


@pytest.fixture
def wrapper(app):
    return NPlusOneMiddleware(app)


@pytest.fixture
def client(routes, wrapper):
    return webtest.TestApp(wrapper)


class TestNPlusOneMiddleware:

    def test_many_to_one(self, objects, client):
        with pytest.raises(exceptions.NPlusOneError):
            client.get('/many_to_one/')

    def test_many_to_one_one(self, objects, client):
        client.get('/many_to_one_one/')
