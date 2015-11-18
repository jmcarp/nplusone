*********
Changelog
*********

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
