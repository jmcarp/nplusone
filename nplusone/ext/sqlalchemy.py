# -*- coding: utf-8 -*-

from __future__ import absolute_import

import itertools

from sqlalchemy.orm import query
from sqlalchemy.orm import attributes
from sqlalchemy.orm import strategies

from nplusone.core import signals


def to_key(instance):
    model = type(instance)
    columns = model.__table__.primary_key.columns
    return ':'.join(
        [model.__name__] +
        [format(getattr(instance, column.key)) for column in columns]
    )


def parse_load(args, kwargs, context, ret):
    return [
        to_key(row) for row in ret
        if hasattr(row, '__table__')
    ]


def parse_lazy_load(args, kwargs, context):
    loader, state, _ = args
    return loader.parent.class_, to_key(state.object), loader.parent_property.key


def parse_eager_load(args, kwargs, context):
    loader = args[0]
    return loader.parent.class_, loader.key


def parse_attribute_get(args, kwargs, context):
    attr = args[0]
    return attr.class_, attr.key


strategies.LazyLoader._load_for_state = signals.signalify(
    signals.lazy_load,
    strategies.LazyLoader._load_for_state,
    parser=parse_lazy_load,
)


strategies.JoinedLoader._create_eager_join = signals.signalify(
    signals.eager_load,
    strategies.JoinedLoader._create_eager_join,
    parser=parse_eager_load,
)


strategies.SubqueryLoader._apply_joins = signals.signalify(
    signals.eager_load,
    strategies.SubqueryLoader._apply_joins,
    parser=parse_eager_load,
)


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
    if not is_single(self._offset, self._limit):
        signals.load.send(
            signals.get_worker(),
            args=(self, ),
            ret=list(clone),
            parser=parse_load,
        )
    return ret
query.Query.__iter__ = query_iter
