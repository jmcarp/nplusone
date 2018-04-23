# -*- coding: utf-8 -*-

from __future__ import absolute_import

from peewee import BaseQuery
from peewee import SelectQuery
from peewee import ForeignKeyAccessor
from peewee import BackrefAccessor
from peewee import ManyToManyQuery
from peewee import BaseModelSelect
from peewee import database_required

from nplusone.core import signals


def parse_get_object(args, kwargs, context):
    accessor, instance = args
    return accessor.field.model, to_key(instance), accessor.field.name


def parse_reverse_get(args, kwargs, context):
    accessor, instance = args
    return accessor.field.rel_model, to_key(instance), accessor.field.backref


def get_rel_instance(self, instance):
    value = instance.__data__.get(self.name)
    if value is not None or self.name in instance.__rel__:
        if self.name not in instance.__rel__:
            signals.lazy_load.send(
                signals.get_worker(),
                args=(self, instance),
                parser=parse_get_object,
            )
            obj = self.rel_model.get(self.field.rel_field == value)
            instance.__rel__[self.name] = obj
        return instance.__rel__[self.name]
    elif not self.field.null:
        raise self.rel_model.DoesNotExist
    return value
ForeignKeyAccessor.get_rel_instance = get_rel_instance


def backref_get(self, instance, instance_type=None):
    if instance is not None:
        dest = self.field.rel_field.name
        query = (self.rel_model
                .select()
                .where(self.field == getattr(instance, dest)))
        # Mark query with context so that we can emit a `lazyload` signal
        # if evaluated during `BaseQuery.execute`
        query._context = {
            'args': (self, instance),
            'kwargs': {'instance_type', instance_type},
        }
        return query
    return self  # pragma: no cover; pasted from peewee
BackrefAccessor.__get__ = backref_get


def to_key(instance):
    model = type(instance)
    return ':'.join([model.__name__, format(instance.get_id())])


def parse_load(args, kwargs, context, ret):
    return [to_key(row) for row in ret]


def is_single(offset, limit):
    return limit is not None and limit - (offset or 0) == 1


original_model_select_iter = BaseModelSelect.__iter__
def model_select_iter(self):
    if isinstance(self, ManyToManyQuery):
        signals.lazy_load.send(
            signals.get_worker(),
            args=(self._accessor, self._instance),
            parser=parse_get_object,
        )
    return original_model_select_iter(self)
BaseModelSelect.__iter__ = model_select_iter


original_query_execute = BaseQuery.execute
def query_execute(self, database):
    ret = original_query_execute(self, database)
    if hasattr(self, '_context'):
        # Query has been marked as lazy during backref lookup
        signals.lazy_load.send(
            signals.get_worker(),
            args=self._context['args'],
            kwargs=self._context['kwargs'],
            parser=parse_reverse_get,
        )
    if not isinstance(self, SelectQuery):
        return ret
    signal = (
        signals.ignore_load
        if is_single(self._offset, self._limit)
        else signals.load
    )
    signal.send(
        signals.get_worker(),
        args=(self, ),
        ret=list(ret),
        parser=parse_load,
    )
    return ret
BaseQuery.execute = database_required(query_execute)
