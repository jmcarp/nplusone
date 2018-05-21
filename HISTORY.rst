*********
Changelog
*********

1.0.0 (2018-05-20)
==================
* Support Peewee 3.0.
* Add `Profiler` context manager for use without HTTP requests.
* Allow model whitelist with fnmatch patterns.
* Add generic wsgi middleware.

0.9.0 (2017-12-02)
==================
* Support Django 2.0.

0.8.2 (2017-11-27)
==================
* Support standard flask extension initialization. Thanks @dcramer!

0.8.1 (2017-08-13)
==================
* Support new Django middleware interface. Thanks @noisecapella!

0.8.0 (2017-04-10)
==================
* Support Django 1.11.

0.7.3 (2016-10-23)
==================
* Handle varying _populate_full signatures across SQLAlchemy versions. Thanks @mrluanma!
* Update Django test versions.

0.7.2 (2016-06-13)
==================
* Ignore lazy loads on records singly and multiply loaded in same request.
* Handle Django `process_response` when `process_request` not called.

0.7.1 (2016-06-03)
==================
* Fix field name on Django `prefetch_related`.
* Handle iteration over empty results in Django templates.
* Fix model and field introspection on Django many-to-many lookups.
* Ignore lazy loads from `get` and `one`.

0.7.0 (2016-04-18)
==================
* Refactor eager-load checking.
* Fix false positive on empty queries using eager loads.
* Handle eager load checks on nested relationships.
* Backwards-incompatible: Drop support for Django 1.7.

0.6.1 (2016-01-08)
==================
* Handle SQLAlchemy properties and columns with different names.

0.6.0 (2016-01-02)
==================
* Add whitelist options.

0.5.0 (2015-12-27)
==================
* Support Django 1.9.
* Ignore lazy loads on singly-loaded records. Thanks @twidi!

0.4.0 (2015-11-17)
==================
* Support Django 1.9 beta.

0.3.0 (2015-11-15)
==================
* Optionally raise errors on potentially unnecessary queries.

0.2.1 (2015-11-09)
==================
* Fix bug on iterating over Django one-to-many relationships. Thanks @orgkhnargh!

0.2.0 (2015-07-07)
==================
* Detect unused eager loads in SQLAlchemy and Django.
* Handle concurrent requests in Django and Flask-SQLAlchemy.
* Handle false-positive lazy loads on prefetching in Django.
* Fix field names on unnamed reverse relations in Django.
* Update documentation.

0.1.0 (2015-06-29)
==================
* First release.
* Support for SQLAlchemy, Peewee, and the Django ORM.
