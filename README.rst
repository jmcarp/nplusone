========
nplusone
========

.. image:: https://img.shields.io/pypi/v/nplusone.svg
    :target: https://img.shields.io/pypi/v/nplusone.svg
    :alt: Latest version

.. image:: https://img.shields.io/travis/jmcarp/nplusone/master.svg
    :target: https://img.shields.io/travis/jmcarp/nplusone/master.svg
    :alt: Travis-CI

.. image:: https://img.shields.io/codecov/c/github/jmcarp/nplusone/master.svg
    :target: https://img.shields.io/codecov/c/github/jmcarp/nplusone/master.svg
    :alt: Code coverage

nplusone is a library for detecting the n+1 queries problem in Python ORMs, including SQLAlchemy, Peewee, and the Django ORM.

The Problem
===========

Many object-relational mapping (ORM) libraries default to lazy loading for relationships. This pattern can be efficient when related rows are rarely accessed, but quickly becomes inefficient as relationships are accessed more frequently. In these cases, loading related rows eagerly using a ``JOIN`` can be vastly more performant. Unfortunately, understanding when to use lazy versus eager loading can be challenging: you might not notice the problem until your app has slowed to a crawl.

``nplusone`` is an ORM profiling tool to help diagnose and improve poor performance caused by inappropriate lazy loading. ``nplusone`` monitors applications using Django or SQLAlchemy and sends warnings when potentially expensive lazy loads are emitted. It can identify the offending relationship attribute and specific lines of code behind the problem, and recommend fixes for better performance.

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

Add ``nplusone`` to ``INSTALLED_APPS`` ::

    INSTALLED_APPS = (
        ...
        'nplusone.ext.django',
    )

Add ``NPlusOneMiddleware`` ::

    MIDDLEWARE_CLASSES = (
        ...
        'nplusone.ext.django.NPlusOneMiddleware',
    )

Optionally configure logging settings ::

    NPLUSONE_LOGGER = logging.getLogger('nplusone')
    NPLUSONE_LOG_LEVEL = logging.WARN

When your app loads data lazily, ``nplusone`` will emit a warning ::

    Potential n+1 query detected on `<model>.<field>`

Consider using `select_related <https://docs.djangoproject.com/en/1.8/ref/models/querysets/#select-related>`_ or `prefetch_related <https://docs.djangoproject.com/en/1.8/ref/models/querysets/#prefetch-related>`_ in this case.

Flask-SQLAlchemy
****************

Wrap application with ``NPlusOne`` ::

    from flask import Flask
    from nplusone.ext.flask_sqlalchemy import NPlusOne

    app = Flask(__name__)
    NPlusOne(app)

Optionally configure logging settings ::

    app = Flask(__name__)
    app.config['NPLUSONE_LOGGER'] = logging.getLogger('app.nplusone')
    app.config['NPLUSONE_LOG_LEVEL'] = logging.ERROR
    NPlusOne(app)

When your app loads data lazily, ``nplusone`` will emit a warning ::

    Potential n+1 query detected on `<model>.<field>`

Consider using ``subqueryload`` or ``joinedload`` in this case; see SQLAlchemy's guide to `relationship loading <http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html>`_ for complete documentation.

Ignoring Warnings
*****************

To suppress warnings thrown by intentional lazy loading, use the ``ignore`` context manager ::

    from nplusone.core import signals

    with signals.ignore():
        # lazy-load rows
        # ...

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/jmcarp/nplusone/blob/master/LICENSE>`_ file for more details.
