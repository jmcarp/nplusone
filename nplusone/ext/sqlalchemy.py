# -*- coding: utf-8 -*-

from __future__ import absolute_import

from sqlalchemy.orm import attributes
from sqlalchemy.orm import strategies

from nplusone.core import signals


def parse_lazy_load(args, kwargs, context):
    loader = args[0]
    return loader.parent.class_, loader.parent_property.key


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
