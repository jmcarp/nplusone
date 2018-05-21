========
nplusone
========

.. image:: https://img.shields.io/pypi/v/nplusone.svg
    :target: http://badge.fury.io/py/nplusone
    :alt: Latest version

.. image:: https://img.shields.io/travis/jmcarp/nplusone/master.svg
    :target: https://travis-ci.org/jmcarp/nplusone
    :alt: Travis-CI

.. image:: https://img.shields.io/codecov/c/github/jmcarp/nplusone/master.svg
    :target: https://codecov.io/github/jmcarp/nplusone
    :alt: Code coverage

nplusone is a library for detecting the n+1 queries problem in Python ORMs, including SQLAlchemy, Peewee, and the Django ORM.

The Problem
===========

Many object-relational mapping (ORM) libraries default to lazy loading for relationships. This pattern can be efficient when related rows are rarely accessed, but quickly becomes inefficient as relationships are accessed more frequently. In these cases, loading related rows eagerly using a ``JOIN`` can be vastly more performant. Unfortunately, understanding when to use lazy versus eager loading can be challenging: you might not notice the problem until your app has slowed to a crawl.

``nplusone`` is an ORM profiling tool to help diagnose and improve poor performance caused by inappropriate lazy loading. ``nplusone`` monitors applications using Django or SQLAlchemy and sends notifications when potentially expensive lazy loads are emitted. It can identify the offending relationship attribute and specific lines of code behind the problem, and recommend fixes for better performance.

``nplusone`` also detects inappropriate eager loading for Flask-SQLAlchemy and the Django ORM, emitting a warning when related data are eagerly loaded but never accessed within the current request.

Installation
============

::

    pip install -U nplusone

nplusone supports Python >= 2.7 or >= 3.3.

Usage
=====

Note: ``nplusone`` should only be used for development and should not be deployed to production environments.

Django
******

Note: ``nplusone`` supports Django >= 1.8.

Add ``nplusone`` to ``INSTALLED_APPS``: ::

    INSTALLED_APPS = (
        ...
        'nplusone.ext.django',
    )

Add ``NPlusOneMiddleware``: ::

    MIDDLEWARE = (
        'nplusone.ext.django.NPlusOneMiddleware',
        ...
    )

Optionally configure logging settings: ::

    NPLUSONE_LOGGER = logging.getLogger('nplusone')
    NPLUSONE_LOG_LEVEL = logging.WARN

Configure logging handlers: ::

    LOGGING = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'nplusone': {
                'handlers': ['console'],
                'level': 'WARN',
            },
        },
    }

When your app loads data lazily, ``nplusone`` will emit a log message: ::

    Potential n+1 query detected on `<model>.<field>`

Consider using `select_related <https://docs.djangoproject.com/en/1.8/ref/models/querysets/#select-related>`_ or `prefetch_related <https://docs.djangoproject.com/en/1.8/ref/models/querysets/#prefetch-related>`_ in this case.

When your app eagerly loads related data without accessing it, ``nplusone`` will log a warning: ::

    Potential unnecessary eager load detected on `<model>.<field>`

Flask-SQLAlchemy
****************

Wrap application with ``NPlusOne``: ::

    from flask import Flask
    from nplusone.ext.flask_sqlalchemy import NPlusOne

    app = Flask(__name__)
    NPlusOne(app)

Optionally configure logging settings: ::

    app = Flask(__name__)
    app.config['NPLUSONE_LOGGER'] = logging.getLogger('app.nplusone')
    app.config['NPLUSONE_LOG_LEVEL'] = logging.ERROR
    NPlusOne(app)

When your app loads data lazily, ``nplusone`` will emit a log message: ::

    Potential n+1 query detected on `<model>.<field>`

Consider using ``subqueryload`` or ``joinedload`` in this case; see SQLAlchemy's guide to `relationship loading <http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html>`_ for complete documentation.

When your app eagerly loads related data without accessing it, ``nplusone`` will log a warning: ::

    Potential unnecessary eager load detected on `<model>.<field>`

WSGI
****

For other frameworks that follow the WSGI specification, wrap your application with `NPlusOneMiddleware`. You must also import the relevant ``nplusone`` extension for your ORM: ::

    import bottle
    from nplusone.ext.wsgi import NPlusOneMiddleware
    import nplusone.ext.sqlalchemy

    app = NPlusOneMiddleware(bottle.app())

Generic
*******

The integrations above are coupled to the request-response cycle. To use ``nplusone`` outside the context of an HTTP request, use the ``Profiler`` context manager: You must also import the relevant ``nplusone`` extension for your ORM: ::

    from nplusone.core import profiler
    import nplusone.ext.sqlalchemy

    with profiler.Profiler():
        ...

Customizing notifications
*************************

By default, ``nplusone`` logs all potentially unnecessary queries using a logger named "nplusone". When the `NPLUSONE_RAISE` configuration option is set, ``nplusone`` will also raise an ``NPlusOneError``. This can be used to force all automated tests involving unnecessary queries to fail. ::

    # Django config
    NPLUSONE_RAISE = True

    # Flask config
    app.config['NPLUSONE_RAISE'] = True

The exception type can also be specified, if desired, using the ``NPLUSONE_ERROR`` option.

Ignoring notifications
**********************

To ignore notifications from ``nplusone`` globally, configure the whitelist using the `NPLUSONE_WHITELIST` option: ::

    # Django config
    NPLUSONE_WHITELIST = [
        {'label': 'n_plus_one', 'model': 'myapp.MyModel'}
    ]

    # Flask-SQLAlchemy config
    app.config['NPLUSONE_WHITELIST'] = [
        {'label': 'unused_eager_load', 'model': 'MyModel', 'field': 'my_field'}
    ]

You can whitelist models by exact name or by `fnmatch <https://docs.python.org/3/library/fnmatch.html>`_ patterns: ::

    # Django config
    NPLUSONE_WHITELIST = [
        {'model': 'myapp.*'}
    ]

To suppress notifications locally, use the ``ignore`` context manager: ::

    from nplusone.core import signals

    with signals.ignore(signals.lazy_load):
        # lazy-load rows
        # ...

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/jmcarp/nplusone/blob/master/LICENSE>`_ file for more details.
