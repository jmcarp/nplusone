*********
Changelog
*********

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
