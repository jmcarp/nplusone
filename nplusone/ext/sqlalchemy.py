# -*- coding: utf-8 -*-

from __future__ import absolute_import

import inspect
import itertools

from sqlalchemy.orm import query
from sqlalchemy.orm import loading
from sqlalchemy.orm import attributes
from sqlalchemy.orm import strategies

from nplusone.core import signals


def to_key(instance):
    model = type(instance)
    return ':'.join(
        [model.__name__] +
        [
            format(instance.__dict__.get(key.key))  # Avoid recursion on __get__
            for key in get_primary_keys(model)
        ]
    )


def get_primary_keys(model):
    mapper = model.__mapper__
    return [
        mapper.get_property_by_column(column)
        for column in mapper.primary_key
    ]


def parse_load(args, kwargs, context, ret):
    return [
        to_key(row) for row in ret
        if hasattr(row, '__table__')
    ]


def parse_lazy_load(args, kwargs, context):
    loader, state, _ = args
    return state.object.__class__, to_key(state.object), loader.parent_property.key


def parse_attribute_get(args, kwargs, context):
    attr, instance = args[:2]
    if instance is None:
        return None
    return attr.class_, attr.key, [to_key(instance)]


strategies.LazyLoader._load_for_state = signals.signalify(
    signals.lazy_load,
    strategies.LazyLoader._load_for_state,
    parser=parse_lazy_load,
)


def parse_populate(args, kwargs, context):
    query_context = args[0]
    state = args[2]
    instance = state.object
    return instance.__class__, context['key'], [to_key(instance)], id(query_context)


# Emit `eager_load` on populating from `joinedload` or `subqueryload`
original_populate_full = loading._populate_full
def _populate_full(*args, **kwargs):
    ret = original_populate_full(*args, **kwargs)
    context = inspect.getcallargs(original_populate_full, *args, **kwargs)
    for key, _ in context['populators'].get('eager', []):
        if context['dict_'].get(key):
            signals.eager_load.send(
                signals.get_worker(),
                args=args,
                kwargs=kwargs,
                context={'key': key},
                parser=parse_populate,
            )
    return ret
loading._populate_full = _populate_full


attributes.InstrumentedAttribute.__get__ = signals.signalify(
    signals.touch,
    attributes.InstrumentedAttribute.__get__,
    parser=parse_attribute_get,
)


def is_single(offset, limit):
    return limit is not None and limit - (offset or 0) == 1


original_query_iter = query.Query.__iter__
def query_iter(self):
    ret, clone = itertools.tee(original_query_iter(self))
    signal = (
        signals.ignore_load
        if is_single(self._offset, self._limit)
        else signals.load
    )
    signal.send(
        signals.get_worker(),
        args=(self, ),
        ret=list(clone),
        parser=parse_load,
    )
    return ret
query.Query.__iter__ = query_iter


def parse_get(args, kwargs, context, ret):
    return [to_key(ret)] if hasattr(ret, '__table__') else []


# Ignore records loaded during `one`
for method in ['one_or_none', 'one']:
    try:
        original = getattr(query.Query, method)
    except AttributeError:
        continue
    decorated = signals.signalify(signals.ignore_load, original, parse_get)
    setattr(query.Query, method, decorated)
