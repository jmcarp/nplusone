========
nplusone
========

.. image:: https://badge.fury.io/py/nplusone.png
    :target: http://badge.fury.io/py/nplusone
    :alt: Latest version

.. image:: https://travis-ci.org/jmcarp/nplusone.png?branch=master
    :target: https://travis-ci.org/jmcarp/nplusone
    :alt: Travis-CI

.. image:: https://codecov.io/github/jmcarp/nplusone/coverage.svg
    :target: https://codecov.io/github/jmcarp/nplusone
    :alt: Code coverage

nplusone is a library for detecting the n+1 queries problem in Python ORMs, including SQLAlchemy and the Django ORM.

The Problem
===========

Many object-relational mapping (ORM) libraries default to lazy loading for relationships. This pattern can be efficient when related rows are rarely accessed, but quickly becomes inefficient as relationships are accessed more frequently. In these cases, loading related rows eagerly using a ``JOIN`` can be vastly more performant. Unfortunately, understanding when to use lazy versus eager loading can be challenging: you might not notice the problem until your app has slowed to a crawl.

``nplusone`` is an ORM profiling tool to help diagnose and improve poor performance caused by inappropriate lazy loading. ``nplusone`` monitors applications using Django or SQLAlchemy and sends warnings when potentially expensive lazy loads are emitted. It can identify the offending relationship attribute and specific lines of code behind the problem, and recommend fixes for better performance.

Usage
=====

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

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/jmcarp/nplusone/blob/master/LICENSE>`_ file for more details.
