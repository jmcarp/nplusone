# -*- coding: utf-8 -*-

import mock
import flask
import pytest
import webtest
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy

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


@pytest.fixture
def app(db, models, logger):
    app = flask.Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['NPLUSONE_LOGGER'] = logger
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def wrapper(app):
    return NPlusOne(app)


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

    @app.route('/many_to_one_first/')
    def many_to_one_first():
        user = models.User.query.first()
        return str(user.addresses)

    @app.route('/many_to_one_ignore/')
    def many_to_one_ignore():
        with wrapper.ignore('lazy_load'):
            users = models.User.query.all()
            return str(users[0].addresses)

    @app.route('/many_to_many/')
    def many_to_many():
        users = models.User.query.all()
        return str(users[0].hobbies)

    @app.route('/many_to_many_impossible/')
    def many_to_many_impossible():
        user = models.User.query.first()
        users = models.User.query.all()  # noqa
        return str(user.hobbies)

    @app.route('/many_to_many_impossible_one/')
    def many_to_many_impossible_one():
        user = models.User.query.one()
        users = models.User.query.all()  # noqa
        return str(user.hobbies)

    @app.route('/eager_join/')
    def eager_join():
        users = models.User.query.options(sa.orm.subqueryload('hobbies')).all()
        return str(users[0].hobbies if users else None)

    @app.route('/eager_subquery/')
    def eager_subquery():
        users = models.User.query.options(sa.orm.subqueryload('hobbies')).all()
        # Touch class-level descriptor to exercise `None` instance checks
        print(models.User.hobbies)
        return str(users[0].hobbies if users else None)

    @app.route('/eager_join_unused/')
    def eager_join_unused():
        users = models.User.query.options(sa.orm.joinedload('hobbies')).all()
        return str(users[0])

    @app.route('/eager_subquery_unused/')
    def eager_subquery_unused():
        users = models.User.query.options(sa.orm.subqueryload('hobbies')).all()
        return str(users[0])

    @app.route('/eager_nested/')
    def eager_nested():
        hobbies = models.Hobby.query.options(
            sa.orm.joinedload(models.Hobby.users).joinedload(
                models.User.addresses,
            )
        ).all()
        return str(hobbies[0].users[0].addresses)

    @app.route('/eager_nested_unused/')
    def eager_nested_unused():
        hobbies = models.Hobby.query.options(
            sa.orm.joinedload(models.Hobby.users).joinedload(
                models.User.addresses,
            )
        ).all()
        return str(hobbies[0])


@pytest.fixture
def client(app, routes, wrapper):
    return webtest.TestApp(app)


class TestNPlusOne:

    def test_many_to_one(self, objects, client, logger):
        client.get('/many_to_one/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.addresses' in args[1]

    def test_many_to_one_one(self, objects, client, logger):
        client.get('/many_to_one_one/')
        assert not logger.log.called

    def test_many_to_one_first(self, objects, client, logger):
        client.get('/many_to_one_first/')
        assert not logger.log.called

    def test_many_to_one_ignore(self, objects, client, logger):
        client.get('/many_to_one_ignore/')
        assert not logger.log.called

    def test_many_to_many(self, objects, client, logger):
        client.get('/many_to_many/')
        assert len(logger.log.call_args_list) == 1
        args = logger.log.call_args[0]
        assert 'User.hobbies' in args[1]

    def test_many_to_many_impossible(self, objects, client, logger):
        client.get('/many_to_many_impossible/')
        assert not logger.log.called

    def test_many_to_many_impossible_one(self, objects, client, logger):
        client.get('/many_to_many_impossible_one/')
        assert not logger.log.called

    def test_eager_join(self, objects, client, logger):
        client.get('/eager_join/')
        assert not logger.log.called

    def test_eager_subquery(self, objects, client, logger):
        client.get('/eager_subquery/')
        assert not logger.log.called

    def test_eager_join_empty(self, models, objects, client, logger):
        models.User.query.delete()
        client.get('/eager_join/')
        assert not logger.log.called

    def test_eager_subquery_empty(self, models, objects, client, logger):
        models.User.query.delete()
        client.get('/eager_subquery/')
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

    def test_eager_nested_unused(self, app, wrapper, objects, client, logger):
        client.get('/eager_nested/')
        assert not logger.log.called

    def test_eager_nested(self, app, wrapper, objects, client, logger):
        client.get('/eager_nested_unused/')
        assert len(logger.log.call_args_list) == 2
        calls = [call[0] for call in logger.log.call_args_list]
        assert any('Hobby.users' in call[1] for call in calls)
        assert any('User.addresses' in call[1] for call in calls)

    def test_many_to_many_raise(self, app, wrapper, objects, client, logger):
        app.config['NPLUSONE_RAISE'] = True
        with pytest.raises(exceptions.NPlusOneError):
            client.get('/many_to_many/')

    def test_many_to_many_whitelist(self, app, wrapper, objects, client, logger):
        app.config['NPLUSONE_WHITELIST'] = [{'model': 'User'}]
        client.get('/many_to_many/')
        assert not logger.log.called

    def test_many_to_many_whitelist_wildcard(self, app, wrapper, objects, client, logger):
        app.config['NPLUSONE_WHITELIST'] = [{'model': 'U*r'}]
        client.get('/many_to_many/')
        assert not logger.log.called

    def test_many_to_many_whitelist_decoy(self, app, wrapper, objects, client, logger):
        app.config['NPLUSONE_WHITELIST'] = [{'model': 'Hobby'}]
        client.get('/many_to_many/')
        assert logger.log.called
